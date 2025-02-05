from app import db, GroceryList, GroceryItem
from collections import Counter
import google.generativeai as genai

# 🔴 Hardcode API key for now (replace with dotenv later)
genai.configure(api_key="your-api-key-here")

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