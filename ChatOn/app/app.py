from flask import Flask, request, render_template, redirect, session, jsonify, abort
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
from contextlib import contextmanager
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'Abi2003#')

RASA_API_URL = 'http://localhost:5005/webhooks/rest/webhook'

# ---------------------------------
# Database Connection Helper
# ---------------------------------
@contextmanager
def db_cursor(dictionary=False):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="product_data",
        port=3308
    )
    cursor = db.cursor(dictionary=dictionary)
    try:
        yield cursor
        db.commit()
    finally:
        cursor.close()
        db.close()

# ---------------------------------
# Chatbot Route
# ---------------------------------
@app.route('/chatbot')
def chatbot():
    return render_template("chatbot.html")


@app.route('/webhook', methods=['POST'])
def webhook():
    user_message = request.json['message']
    print("User message:", user_message)
    try:
        rasa_response = requests.post(RASA_API_URL, json={'message': user_message})
        rasa_response_json = rasa_response.json()
        print("Rasa response:", rasa_response_json)
        bot_response = rasa_response_json[0]['text'] if rasa_response_json else "Sorry, I did not understand that."
    except Exception as e:
        print("Error contacting Rasa:", e)
        bot_response = "Sorry, the chatbot service is unavailable right now."
    return jsonify({"response": bot_response})

# ---------------------------------
# Index Route
# ---------------------------------
@app.route('/')
def index():
    return render_template("index.html")

# ---------------------------------
# Admin Role Decorator
# ---------------------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# ---------------------------------
# Signup Route
# ---------------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password_input = request.form['password']
        shop_name = request.form['shop_name'].strip()
        shop_address = request.form['shop_address'].strip()
        contact_email = request.form['contact_email'].strip()
        phone_number = request.form['phone_number'].strip()
        shop_description = request.form['shop_description'].strip()
        role = 'user'

        # Validate required fields
        if not username:
            return render_template("signup.html", error="Username is required.")
        if not password_input:
            return render_template("signup.html", error="Password is required.")
        if not shop_name:
            return render_template("signup.html", error="Shop name is required.")
        if not shop_address:
            return render_template("signup.html", error="Shop address is required.")
        if not contact_email:
            return render_template("signup.html", error="Contact email is required.")
        if not phone_number:
            return render_template("signup.html", error="Phone number is required.")

        password = generate_password_hash(password_input)

        with db_cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return render_template("signup.html", error="Username already exists. Please choose another.")

            try:
                cursor.execute('''
                    INSERT INTO users (username, password, shop_name, shop_address, contact_email, phone_number, shop_description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (username, password, shop_name, shop_address, contact_email, phone_number, shop_description))
                user_id = cursor.lastrowid

                session['user_id'] = user_id
                session['username'] = username
                session['role'] = role

                return redirect('/dashboard')
            except mysql.connector.IntegrityError as err:
                if err.errno == 1062:
                    return render_template("signup.html", error="Username already exists.")
                return render_template("signup.html", error=f"Database error: {err}")

    return render_template("signup.html")




# ---------------------------------
# Login Route
# ---------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password_input = request.form.get('password')

        with db_cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user['password'], password_input):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user.get('role', 'user')
            return redirect('/dashboard')
        else:
            return render_template("login.html", error="Invalid username or password.")
    return render_template("login.html")

# ---------------------------------
# Logout
# ---------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------------------------------
# Dashboard
# ---------------------------------
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    if session.get('role') == 'admin':
        return redirect('/admin')

    with db_cursor(dictionary=True) as cursor:
        # Handle product submission
        if request.method == 'POST':
            product_name = request.form['product_name']
            brand = request.form['brand']
            size = request.form['size']
            price = request.form['price']
            description = request.form['description']
            cursor.execute("""
                INSERT INTO product_catalog
                (user_id, `Product Name`, Brand, Size, SellPrice, Description)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, product_name, brand, size, price, description))

        # Fetch products for this user
        cursor.execute("SELECT * FROM product_catalog WHERE user_id = %s", (user_id,))
        products = cursor.fetchall()

        # Fetch user profile info
        cursor.execute("""
            SELECT shop_name, shop_address, contact_email, phone_number, shop_description
            FROM users
            WHERE id = %s
        """, (user_id,))
        user_profile = cursor.fetchone()

        # Fetch feedbacks for this user's products
        cursor.execute("""
            SELECT 
                COALESCE(pc.`Product Name`, f.product_name) AS product_name,
                f.feedback_text,
                f.created_at
            FROM feedback f
            LEFT JOIN product_catalog pc ON f.product_id = pc.id
            WHERE (pc.user_id = %s OR f.product_id IS NULL)
            ORDER BY f.created_at DESC
            LIMIT 20
        """, (user_id,))
        feedbacks = cursor.fetchall()

    return render_template(
        "dashboard.html",
        username=session['username'],
        products=products,
        user=user_profile,
        feedbacks=feedbacks
    )


# ---------------------------------
# Update Product
# ---------------------------------
@app.route('/update_product/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    with db_cursor(dictionary=True) as cursor:
        if request.method == 'POST':
            product_name = request.form['product_name']
            brand = request.form['brand']
            size = request.form['size']
            price = request.form['price']
            description = request.form['description']

            cursor.execute("""
                UPDATE product_catalog
                SET `Product Name`=%s, Brand=%s, Size=%s, SellPrice=%s, Description=%s
                WHERE id=%s AND user_id=%s
            """, (product_name, brand, size, price, description, product_id, user_id))
            return redirect('/dashboard')

        cursor.execute("""
            SELECT * FROM product_catalog
            WHERE id = %s AND user_id = %s
        """, (product_id, user_id))
        product = cursor.fetchone()
        if not product:
            return "Product not found."

    return render_template('update_product.html', product=product)

# ---------------------------------
# Delete Product
# ---------------------------------
@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    with db_cursor() as cursor:
        cursor.execute("""
            DELETE FROM product_catalog
            WHERE id = %s AND user_id = %s
        """, (product_id, user_id))

    return redirect('/dashboard')

# ---------------------------------
# Admin Panel
# ---------------------------------
@app.route('/admin')
@admin_required
def admin_panel():
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("SELECT id, username, role FROM users")
        users = cursor.fetchall()
        cursor.execute("SELECT * FROM product_catalog")
        products = cursor.fetchall()

    return render_template("admin_panel.html", users=users, products=products)



# Run App

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=3000)








# To run Rasa server separately:
# rasa run --enable-api --cors "*" --model models/20250714-171419-inverted-pantone.tar.gz



# rasa shell nlu --model models/20250714-171419-inverted-pantone.tar.gz





















