import requests
import os
import json

key = os.getenv('USDA_API_KEY')
def apiParse(foodName):
    print(key)
    if key is None:
        raise ValueError("USDA_API_KEY not set in environment variables.")
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={key}&query={foodName}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'foods' in data:
            first_fdc_id = data['foods'][0]['fdcId']
            return first_fdc_id
        else:
            return None 
    else:
        print(f"Error: {response.status_code} - {response.text}")
    
def getFoodData(fdcId):
    url = f"https://api.nal.usda.gov/fdc/v1/food/{fdcId}?api_key={key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        nutrientTypes = [x for x in data['labelNutrients']]
        nutrients = {x : data["labelNutrients"][x]["value"] for x in nutrientTypes}
        return nutrients 
    else:
        return "Invalid fdcID"
getFoodData(apiParse())


