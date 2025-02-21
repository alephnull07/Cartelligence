import requests
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# FoodData Central API settings
USDA_API_KEY = os.getenv("USDA_API_KEY")
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

def search_food_central(query):
    """Search the FoodData Central API for a given query."""
    params = {
        "api_key": USDA_API_KEY,
        "query": query,
        "pageSize": 5,  # Limit results to 5 items
    }
    response = requests.get(USDA_BASE_URL, params=params)
    if response.status_code == 200:
        return response.json().get("foods", [])
    else:
        print(f"Error fetching data from FoodData Central: {response.status_code}")
        return []

def get_nutritional_info(food_id):
    """Fetch detailed nutritional info for a specific food item from FoodData Central."""
    url = f"https://api.nal.usda.gov/fdc/v1/food/{food_id}"
    params = {"api_key": USDA_API_KEY}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        food_data = response.json()
        food_name = food_data.get("description", "Unknown Food")
        
        # Extract relevant nutritional data
        nutrients = food_data.get("foodNutrients", [])
        nutritional_info = {
            "food_name": food_name,
            "calories": next((n.get("amount") for n in nutrients if n.get("nutrientName") == "Energy"), "N/A"),
            "protein": next((n.get("amount") for n in nutrients if n.get("nutrientName") == "Protein"), "N/A"),
            "carbs": next((n.get("amount") for n in nutrients if n.get("nutrientName") == "Carbohydrate, by difference"), "N/A"),
            "fats": next((n.get("amount") for n in nutrients if n.get("nutrientName") == "Total lipid (fat)"), "N/A"),
            "fiber": next((n.get("amount") for n in nutrients if n.get("nutrientName") == "Fiber, total dietary"), "N/A"),
            "sugar": next((n.get("amount") for n in nutrients if n.get("nutrientName") == "Sugars, total"), "N/A"),
            "sodium": next((n.get("amount") for n in nutrients if n.get("nutrientName") == "Sodium, Na"), "N/A"),
        }
        
        return nutritional_info
    else:
        print(f"Error fetching nutritional info: {response.status_code}")
        return None

def generate_alternatives(ingredient, dietary_restrictions, budget):
    """Generate alternatives using FoodData Central and Gemini."""
    # Step 1: Search for alternatives in FoodData Central
    search_results = search_food_central(ingredient)
    if not search_results:
        return []

    # Step 2: Filter results based on dietary restrictions and budget
    alternatives = []
    for food in search_results:
        food_name = food.get("description", "")
        food_id = food.get("fdcId", "")
        nutritional_info = get_nutritional_info(food_id)

        if nutritional_info:
            # Extract relevant nutritional data
            nutrients = nutritional_info.get("foodNutrients", [])
            calories = next((n.get("amount") for n in nutrients if n.get("nutrientName") == "Energy"), "N/A")
            protein = next((n.get("amount") for n in nutrients if n.get("nutrientName") == "Protein"), "N/A")
            carbs = next((n.get("amount") for n in nutrients if n.get("nutrientName") == "Carbohydrate, by difference"), "N/A")
            fats = next((n.get("amount") for n in nutrients if n.get("nutrientName") == "Total lipid (fat)"), "N/A")

            # Add to alternatives list
            alternatives.append({
                "name": food_name,
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fats": fats,
                "price": "N/A"  # Placeholder for price (can be fetched from another API or hardcoded)
            })

    # Step 3: Use Gemini to refine the results
    prompt = f"""
    A user is looking for alternatives to {ingredient} with the following dietary restrictions: {dietary_restrictions} and a budget of {budget}.
    Here are some potential alternatives from the FoodData Central API:
    {alternatives}

    Refine this list to only include items that fit the user's dietary restrictions and budget. Return the refined list as a Python list of dictionaries.
    """
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    refined_alternatives = eval(response.text)  # Convert the response to a list of dictionaries

    return refined_alternatives