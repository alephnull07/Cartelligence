from app import db, GroceryList, GroceryItem
from collections import Counter
import google.generativeai as genai
import re
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Retrieve the API key from the environment
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

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

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    
    return response.text.strip()  # Clean output
model = genai.GenerativeModel("gemini-1.5-flash")
convo = model.start_chat(history=[])


def generateRecipe(diet, budget):
    prompt = (
        "Generate an easy-to-follow recipe based on the following dietary restrictions: "
        f"{diet} and budget constraints: {budget}. "
        "The recipe should be suitable for a beginner cook and should not require any special equipment. "
        "Based on the recipe, generate a comprehensive grocery list that includes all necessary ingredients. "
        "Capitalize the first letter of each ingredient. "
        "Avoid umbrella terms like 'bean (black, pinto, canned)' or 'frozen fruit'. Instead, list individual items like 'black beans' or 'strawberries'. "
        "Format the response exactly as follows:\n\n"
        "Title:\n(Include a title for the recipe)\n\n"
        "Instructions:\n(Provide the step-by-step instructions as a single paragraph.)\n\n"
        "Ingredients:\n(List each ingredient on a new line, without numbering or bullet points.)"
    )

    response = convo.send_message(prompt)

    response_text = convo.last.text.strip()

    print("Raw AI Response:\n", response_text)  # Debugging output

    # Extract title, instructions, and ingredients using regex
    title_match = re.search(r"(?i)Title:\s*(.+?)(?=\nInstructions:|\nIngredients:|$)", response_text, re.DOTALL)
    instructions_match = re.search(r"(?i)Instructions:\s*(.+?)(?=\nIngredients:|$)", response_text, re.DOTALL)
    ingredients_match = re.search(r"(?i)Ingredients:\s*(.+)", response_text, re.DOTALL)

    # Debugging output for regex matches
    print("Title Match:", title_match)
    print("Instructions Match:", instructions_match)
    print("Ingredients Match:", ingredients_match)

    if not title_match or not instructions_match or not ingredients_match:
        print("Error: Could not parse AI response properly.")
        return "Error: Unable to generate recipe.", [], ""

    title = title_match.group(1).strip()
    instructions = instructions_match.group(1).strip()
    ingredients = [line.strip() for line in ingredients_match.group(1).split("\n") if line.strip()]
    
    return instructions, ingredients, title


def customRecipe(name, diet, budget):
    prompt = (
        "Generate an easy-to-follow recipe based on the following food name: "
        f"{name}. and dietary restrictions: {diet} and budget constraints: {budget}. "
        "The recipe should be suitable for a beginner cook and should not require any special equipment. "
        "Based on the recipe, generate a comprehensive grocery list that includes all necessary ingredients. "
        "Capitalize the first letter of each ingredient. "
        "Avoid umbrella terms like 'bean (black, pinto, canned)' or 'frozen fruit'. Instead, list individual items like 'black beans' or 'strawberries'. "
        "Format the response exactly as follows:\n\n"
        "Title:\n(Include a title for the recipe)\n\n"
        "Instructions:\n(Provide the step-by-step instructions as a single paragraph.)\n\n"
        "Ingredients:\n(List each ingredient on a new line, without numbering or bullet points.)"
    )

    response = convo.send_message(prompt)

    response_text = convo.last.text.strip()

    print("Raw AI Response:\n", response_text)  # Debugging output

    # Extract title, instructions, and ingredients using regex
    title_match = re.search(r"(?i)Title:\s*(.+?)(?=\nInstructions:|\nIngredients:|$)", response_text, re.DOTALL)
    instructions_match = re.search(r"(?i)Instructions:\s*(.+?)(?=\nIngredients:|$)", response_text, re.DOTALL)
    ingredients_match = re.search(r"(?i)Ingredients:\s*(.+)", response_text, re.DOTALL)

    # Debugging output for regex matches
    print("Title Match:", title_match)
    print("Instructions Match:", instructions_match)
    print("Ingredients Match:", ingredients_match)

    if not title_match or not instructions_match or not ingredients_match:
        print("Error: Could not parse AI response properly.")
        return "Error: Unable to generate recipe.", [], ""

    title = title_match.group(1).strip()
    instructions = instructions_match.group(1).strip()
    ingredients = [line.strip() for line in ingredients_match.group(1).split("\n") if line.strip()]
    
    return instructions, ingredients, title


def generateAlternative(ingredient):
    prompt = f"""
    As a nutrition expert, provide 3-4 high-quality alternatives to {ingredient} using the exact format below:

    # Alternatives for {ingredient}

    1. [Alternative Name]: [1-2 sentence description explaining why it's a good substitute, with nutrition comparison]
    2. [Alternative Name]: [1-2 sentence description explaining why it's a good substitute, with nutrition comparison] 
    3. [Alternative Name]: [1-2 sentence description explaining why it's a good substitute, with nutrition comparison]
    
    For each alternative:
    - Provide specific nutritional benefits compared to the original ingredient
    - Include whether it's more budget-friendly, healthier, or has other advantages
    - Mention any taste or texture differences
    - Focus on commonly available substitutes
    """

    model = genai.GenerativeModel("gemini-1.5-flash")
    convo = model.start_chat(history=[])
    response = convo.send_message(prompt)

    return convo.last.text


def generateNutrition(ingredient):
    prompt = f"""
    As a nutrition expert, provide a detailed but concise nutritional analysis of {ingredient} using exactly the format below:

    # Nutrition Facts: {ingredient}

    ## Nutritional Values (per 100g)
    - Calories: [value] kcal
    - Protein: [value]g
    - Carbohydrates: [value]g
    - Fat: [value]g
    - Fiber: [value]g
    - Sugar: [value]g
    - Sodium: [value]mg

    ## Health Benefits
    - [Specific health benefit 1]
    - [Specific health benefit 2]
    - [Specific health benefit 3]

    ## Key Information
    [2-3 sentences with important nutritional context about this food]

    Use accurate nutritional data. Be specific and evidence-based. Respond only with this structured format.
    """

    model = genai.GenerativeModel("gemini-1.5-flash")
    convo = model.start_chat(history=[])
    response = convo.send_message(prompt)
    
    return convo.last.text