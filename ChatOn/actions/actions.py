import mysql.connector
from mysql.connector import Error
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from difflib import SequenceMatcher
from textblob import TextBlob
from typing import Dict, Text, Any, List

# Utility: String similarity
def is_similar(a: str, b: str) -> bool:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.5

# Utility: General column query for matching product names
def query_product_info(cursor, product_name: str, column: str):
    product_name = product_name.strip().lower()
    found_data = []

    query = f"""
        SELECT user_id, `Product Name`, {column}
        FROM product_catalog
    """
    cursor.execute(query)
    for (user_id, db_name, value) in cursor.fetchall():
        if is_similar(product_name, db_name):
            found_data.append(f"User {user_id}: {value}")
    return found_data


class ActionCheckAvailability(Action):
    def name(self) -> str:
        return "action_check_availability"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        entities = tracker.latest_message.get("entities", [])
        new_product = next((e["value"] for e in entities if e["entity"] == "product_name"), None)

        if new_product:
            product_name = new_product.strip().lower()
        else:
            slot_product = tracker.get_slot("product_name")
            product_name = slot_product.strip().lower() if slot_product else None

        if not product_name:
            dispatcher.utter_message("sorry we don't have any product like that/n do you want any other product?")
            return []

        available_users = []
        connection = None
        cursor = None

        try:
            connection = mysql.connector.connect(
                host="localhost", port=3308, user="root",
                password="", database="product_data"
            )
            cursor = connection.cursor()

            cursor.execute("""
                SELECT DISTINCT user_id, `Product Name`
                FROM product_catalog
            """)
            for (user_id, name) in cursor.fetchall():
                if is_similar(product_name, name):
                    available_users.append(f"User {user_id}")

            if available_users:
                dispatcher.utter_message(
                    text=f"The '{product_name}' is available."
                )
                dispatcher.utter_message(
                    response="utter_offer_more_options"
                )
                return [SlotSet("product_name", product_name)]
            else:
                dispatcher.utter_message(
                    text=f"Sorry, we don't have a product named '{product_name}'."
                )
                return [SlotSet("product_name", None)]

        except Error as err:
            dispatcher.utter_message(f"Database error: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()


class ActionGettingPrice(Action):
    def name(self) -> str:
        return "action_getting_price"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        entities = tracker.latest_message.get("entities", [])
        new_product = next((e["value"] for e in entities if e["entity"] == "product_name"), None)

        if new_product:
            product_name = new_product.strip().lower()
        else:
            product_name = tracker.get_slot("product_name")
            if product_name:
                product_name = product_name.strip().lower()

        if not product_name:
            dispatcher.utter_message("sorry we don't have any product like that")
            return []

        connection = None
        cursor = None

        try:
            connection = mysql.connector.connect(
                host="localhost", port=3308, user="root",
                password="", database="product_data"
            )
            cursor = connection.cursor()

            cursor.execute("SELECT `Product Name`, SellPrice FROM product_catalog")
            found = None
            for (db_name, price) in cursor.fetchall():
                if is_similar(product_name, db_name):
                    found = (db_name, price)
                    break

            if found:
                dispatcher.utter_message(
                    text=f"The price of '{found[0]}' is {found[1]}."
                )
                dispatcher.utter_message(
                    response="utter_offer_more_options"
                )
                return [SlotSet("product_name", found[0])]
            else:
                dispatcher.utter_message(
                    text=f"Sorry, we don't have a product named '{product_name}'."
                )
                return [SlotSet("product_name", None)]

        except Error as err:
            dispatcher.utter_message(f"Database error: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()


class ActionQueryBrand(Action):
    def name(self) -> str:
        return "action_getting_brand"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain) -> list:

        entities = tracker.latest_message.get("entities", [])
        new_product = next((e["value"] for e in entities if e["entity"] == "product_name"), None)

        if new_product:
            product_name = new_product.strip().lower()
        else:
            product_name = tracker.get_slot("product_name")
            if product_name:
                product_name = product_name.strip().lower()

        if not product_name:
            dispatcher.utter_message("Please provide the product name.")
            return []

        connection = None
        cursor = None

        try:
            connection = mysql.connector.connect(
                host="localhost", port=3308, user="root",
                password="", database="product_data"
            )
            cursor = connection.cursor()
            results = query_product_info(cursor, product_name, "Brand")

            if results:
                dispatcher.utter_message(
                    text=f"Brand(s) for '{product_name}': {', '.join(results)}."
                )
                dispatcher.utter_message(
                    response="utter_offer_more_options"
                )
                return [SlotSet("product_name", product_name)]
            else:
                dispatcher.utter_message(
                    text=f"Sorry, we don't have a product named '{product_name}'."
                )
                return [SlotSet("product_name", None)]

        except Error as err:
            dispatcher.utter_message(f"Database error: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()


class ActionQueryDescription(Action):
    def name(self) -> str:
        return "action_getting_description"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain) -> list:

        entities = tracker.latest_message.get("entities", [])
        new_product = next((e["value"] for e in entities if e["entity"] == "product_name"), None)

        if new_product:
            product_name = new_product.strip().lower()
        else:
            product_name = tracker.get_slot("product_name")
            if product_name:
                product_name = product_name.strip().lower()

        if not product_name:
            dispatcher.utter_message("Please provide the product name.")
            return []

        connection = None
        cursor = None

        try:
            connection = mysql.connector.connect(
                host="localhost", port=3308, user="root",
                password="", database="product_data"
            )
            cursor = connection.cursor()
            results = query_product_info(cursor, product_name, "Description")

            if results:
                dispatcher.utter_message(
                    text=f"Description(s): {', '.join(results)}."
                )
                dispatcher.utter_message(
                    response="utter_offer_more_options"
                )
                return [SlotSet("product_name", product_name)]
            else:
                dispatcher.utter_message(
                    text=f"Sorry, we don't have a product named '{product_name}'."
                )
                return [SlotSet("product_name", None)]

        except Error as err:
            dispatcher.utter_message(f"Database error: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()


class ActionQuerySize(Action):
    def name(self) -> str:
        return "action_getting_size"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain) -> list:

        entities = tracker.latest_message.get("entities", [])
        new_product = next((e["value"] for e in entities if e["entity"] == "product_name"), None)

        if new_product:
            product_name = new_product.strip().lower()
        else:
            product_name = tracker.get_slot("product_name")
            if product_name:
                product_name = product_name.strip().lower()

        if not product_name:
            dispatcher.utter_message("Please provide the product name.")
            return []

        connection = None
        cursor = None

        try:
            connection = mysql.connector.connect(
                host="localhost", port=3308, user="root",
                password="", database="product_data"
            )
            cursor = connection.cursor()
            results = query_product_info(cursor, product_name, "Size")

            if results:
                dispatcher.utter_message(
                    text=f"Size(s): {', '.join(results)}."
                )
                dispatcher.utter_message(
                    response="utter_offer_more_options"
                )
                return [SlotSet("product_name", product_name)]
            else:
                dispatcher.utter_message(
                    text=f"Sorry, we don't have a product named '{product_name}'."
                )
                return [SlotSet("product_name", None)]

        except Error as err:
            dispatcher.utter_message(f"Database error: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

class ActionQueryLocation(Action):
    def name(self) -> str:
        return "action_getting_location"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain) -> list:

        entities = tracker.latest_message.get("entities", [])
        new_product = next((e["value"] for e in entities if e["entity"] == "product_name"), None)

        if new_product:
            product_name = new_product.strip().lower()
        else:
            product_name = tracker.get_slot("product_name")
            if product_name:
                product_name = product_name.strip().lower()

        if not product_name:
            dispatcher.utter_message("we don't have a relevent product.")
            return []

        connection = None
        cursor = None

        try:
            connection = mysql.connector.connect(
                host="localhost", port=3308, user="root",
                password="", database="product_data"
            )
            cursor = connection.cursor()

            owner_id = None
            cursor.execute("""
                SELECT DISTINCT user_id, `Product Name`
                FROM product_catalog
            """)
            for (uid, db_name) in cursor.fetchall():
                if is_similar(product_name, db_name):
                    owner_id = uid
                    product_name = db_name
                    break

            if owner_id is None:
                dispatcher.utter_message(
                    text=f"Sorry, we don't have a product named '{product_name}'."
                )
                return [SlotSet("product_name", None)]

            cursor.execute("SELECT shop_address FROM users WHERE id = %s", (owner_id,))
            result = cursor.fetchone()
            if result:
                dispatcher.utter_message(
                    text=f"The shop location is: {result[0]}"
                )
                dispatcher.utter_message(
                    response="utter_offer_more_options"
                )
                return [SlotSet("product_name", product_name)]
            else:
                dispatcher.utter_message("No shop address found.")
                return [SlotSet("product_name", product_name)]

        except Error as err:
            dispatcher.utter_message(f"Database error: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()


class ActionQueryContact(Action):
    def name(self) -> str:
        return "action_getting_contact"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain) -> list:

        entities = tracker.latest_message.get("entities", [])
        new_product = next((e["value"] for e in entities if e["entity"] == "product_name"), None)

        if new_product:
            product_name = new_product.strip().lower()
        else:
            product_name = tracker.get_slot("product_name")
            if product_name:
                product_name = product_name.strip().lower()

        if not product_name:
            dispatcher.utter_message("Please provide the product name.")
            return []

        connection = None
        cursor = None

        try:
            connection = mysql.connector.connect(
                host="localhost", port=3308, user="root",
                password="", database="product_data"
            )
            cursor = connection.cursor()

            owner_id = None
            cursor.execute("""
                SELECT DISTINCT user_id, `Product Name`
                FROM product_catalog
            """)
            for (uid, db_name) in cursor.fetchall():
                if is_similar(product_name, db_name):
                    owner_id = uid
                    product_name = db_name
                    break

            if owner_id is None:
                dispatcher.utter_message(
                    text=f"Sorry, we don't have a product named '{product_name}'."
                )
                return [SlotSet("product_name", None)]

            cursor.execute(
                "SELECT contact_email, phone_number FROM users WHERE id = %s", (owner_id,)
            )
            result = cursor.fetchone()

            if result:
                contact_email, phone_number = result
                msg = "Contact info:\n"
                if contact_email:
                    msg += f"- Email: {contact_email}\n"
                if phone_number:
                    msg += f"- Phone: {phone_number}"
                dispatcher.utter_message(text=msg.strip())
                dispatcher.utter_message(
                    text="Would you like to know anything else about this product?"
                )
                return [SlotSet("product_name", product_name)]
            else:
                dispatcher.utter_message("No contact information found.")
                return [SlotSet("product_name", product_name)]

        except Error as err:
            dispatcher.utter_message(f"Database error: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()


class ActionStoreFeedback(Action):
    def name(self) -> str:
        return "action_store_feedback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        entities = tracker.latest_message.get("entities", [])
        new_product = next((e["value"] for e in entities if e["entity"] == "product_name"), None)

        if new_product:
            product_name = new_product.strip().lower()
        else:
            product_name = tracker.get_slot("product_name")

        feedback_text = tracker.latest_message.get("text")
        sentiment = tracker.get_slot("sentiment")

        if not sentiment and feedback_text:
            blob = TextBlob(feedback_text)
            polarity = blob.sentiment.polarity
            if polarity >= 0.2:
                sentiment = "positive"
            elif polarity <= -0.2:
                sentiment = "negative"
            else:
                sentiment = "neutral"

        if not product_name or not feedback_text or not sentiment:
            dispatcher.utter_message(
                text="Please provide the product name and your feedback."
            )
            return []

        connection = None
        cursor = None

        try:
            connection = mysql.connector.connect(
                host="localhost", port=3308, user="root",
                password="", database="product_data"
            )
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO feedback (product_name, feedback_text, sentiment)
                VALUES (%s, %s, %s)
            """, (product_name, feedback_text, sentiment))
            connection.commit()

            dispatcher.utter_message(
                text=f"Thank you! Your feedback for '{product_name}' has been recorded."
            )

            return [
                SlotSet("product_name", product_name),
                SlotSet("sentiment", None)
            ]

        except Error as err:
            dispatcher.utter_message(f"Database error: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()


class ActionQueryFeedbackSummary(Action):
    def name(self) -> str:
        return "action_query_feedback_summary"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain) -> List[Dict[Text, Any]]:

        entities = tracker.latest_message.get("entities", [])
        new_product = next((e["value"] for e in entities if e["entity"] == "product_name"), None)

        if new_product:
            product_name = new_product.strip().lower()
        else:
            product_name = tracker.get_slot("product_name")
            if product_name:
                product_name = product_name.strip().lower()

        if not product_name:
            dispatcher.utter_message("Please provide the product name.")
            return []

        connection = None
        cursor = None

        try:
            connection = mysql.connector.connect(
                host="localhost", port=3308, user="root",
                password="", database="product_data"
            )
            cursor = connection.cursor()

            cursor.execute("""
                SELECT sentiment, COUNT(*) FROM feedback
                WHERE product_name = %s
                GROUP BY sentiment
            """, (product_name,))
            rows = cursor.fetchall()

            if not rows:
                dispatcher.utter_message(
                    text=f"Sorry, we don't have a product named '{product_name}'."
                )
                return [SlotSet("product_name", None)]

            summary = {s: c for (s, c) in rows}
            pos = summary.get("positive", 0)
            neg = summary.get("negative", 0)
            neu = summary.get("neutral", 0)

            total = pos + neg + neu

            if total == 0:
                dispatcher.utter_message(
                    text=f"No feedback data available for '{product_name}'."
                )
            elif pos > neg and pos > neu:
                dispatcher.utter_message(
                    text=f"Most customers are satisfied with '{product_name}'."
                )
            elif neg > pos and neg > neu:
                dispatcher.utter_message(
                    text=f"Many customers had concerns about '{product_name}'."
                )
            elif neu >= pos and neu >= neg:
                dispatcher.utter_message(
                    text=f"Feedback for '{product_name}' is mostly neutral."
                )
            else:
                dispatcher.utter_message(
                    text=f"Feedback for '{product_name}' is mixed."
                )

            dispatcher.utter_message(
                text="Would you like to know anything else about this product?"
            )
            return [SlotSet("product_name", product_name)]

        except Error as err:
            dispatcher.utter_message(f"Database error: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

class ActionSearchByDescription(Action):
    def name(self) -> str:
        return "action_search_by_description"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        query_text = tracker.latest_message.get("text")

        if not query_text or len(query_text.strip()) < 3:
            dispatcher.utter_message(
                "Please describe what you're looking for in more detail."
            )
            return []

        connection = None
        cursor = None

        try:
            connection = mysql.connector.connect(
                host="localhost", port=3308, user="root",
                password="", database="product_data"
            )
            cursor = connection.cursor()

            # Full-Text Search Query
            sql = """
                SELECT `Product Name`, Description,
                       MATCH(Description) AGAINST(%s) AS score
                FROM product_catalog
                WHERE MATCH(Description) AGAINST(%s)
                ORDER BY score DESC
                LIMIT 5
            """

            cursor.execute(sql, (query_text, query_text))
            rows = cursor.fetchall()

            if not rows:
                dispatcher.utter_message(
                    "Sorry, I couldn't find any products matching your description."
                )
                return []

            message = "Here are some products I found:\n"
            for (name, description, score) in rows:
                snippet = (description[:80] + "...") if description and len(description) > 80 else description
                message += f"\n• {name}: {snippet}"

            dispatcher.utter_message(message.strip())
            dispatcher.utter_message(
                "Would you like more details about any of these products?"
            )

            return []

        except Error as err:
            dispatcher.utter_message(f"Database error: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
