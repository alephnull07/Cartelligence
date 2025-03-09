from app import db, GroceryList, GroceryItem
from collections import Counter
import google.generativeai as genai

# 🔴 Hardcode API key for now (replace with dotenv later)
genai.configure(api_key="AIzaSyB4XhwtIgPFclhqnxpvH05dBkDNwW0vEi4")

def get_user_items(user_id):
    """Fetch all grocery items from a specific user's grocery lists."""
    items = [item.name for item in GroceryItem.query.join(GroceryList).filter(GroceryList.user_id == user_id).all()]
    return items

def get_most_popular_item_for_user(user_id):
    """Find the most frequently purchased grocery item for a single user."""
    items = get_user_items(user_id)
    
    if not items:
        return "No items found in this user's grocery lists."

    # Step 1: Use local counting first
    item_counts = Counter(items)
    most_common = item_counts.most_common(1)
    if most_common:
        return most_common[0][0]  # Return the most common item

    # Step 2: Ask Gemini for deeper insights
    prompt = f"""
    A user has created multiple grocery lists. Here are all the items they have added:
    {items}

    Identify the single most commonly purchased grocery item by this user and return only its name.
    """

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    
    return response.text.strip()  # Clean output

def generateList(diet, budget):
    prompt = (
    "Generate a grocery list of **strictly five specific ingredients** based on the following dietary restrictions: "
    f"{diet} and budget constraints: {budget}. "
    "Capitalize *the first letter* of each ingredient."
    "Avoid umbrella terms like 'bean (black, pinto, canned)' or 'frozen fruit'. Instead, list individual items like 'black beans' or 'strawberries'. "
    "Format the response strictly as a **comma-separated string**, with no additional text or headings. Separate each entry with commas."
    "Example: 'Black beans, Bananas, Broccoli, Carrots, Eggs'"
    )

    model = genai.GenerativeModel("gemini-pro")
    convo = model.start_chat(history=[])
    response = convo.send_message(prompt)

    return convo.last.text

def generateAlternative(ingredient):
    prompt = (
    "Please concisely find a single substitute for this ingredient: " + ingredient + "."
    "Avoid umbrella terms like 'alternative milk (oat, almond, soy)'. Instead, list an individual item like 'oat milk'."
    )

    model = genai.GenerativeModel("gemini-pro")
    convo = model.start_chat(history=[])
    response = convo.send_message(prompt)

    return convo.last.text

def generateNutrition(ingredient):

    prompt = (
        "Please concisely list the number of calories, carbohydrates, and added sugars (if any) and the amount of protein and sodium in this grocery item: " + f"{ingredient}"
        "Format the response strictly as a **Python string**, with no additional text or headings. Separate each entry with commas."
        "Example: ['100 calories', '20g carbohydrates', '5g added sugars', '10g protein', '200mg sodium']"
    )

    model = genai.GenerativeModel("gemini-pro")
    convo = model.start_chat(history=[])
    response = convo.send_message(prompt)

    return convo.last.text