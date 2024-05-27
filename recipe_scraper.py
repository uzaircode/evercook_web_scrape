from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
from urllib.parse import urlparse
from selenium import webdriver


load_dotenv()

app = Flask(__name__)


class Recipe:
    def __init__(self, name, description, prepTime, cookTime, servings, ingredients, instructionsList, imageUrl, source):
        self.name = name
        self.description = description
        self.prepTime = prepTime
        self.cookTime = cookTime
        self.servings = servings
        self.ingredients = ingredients
        self.instructionsList = instructionsList
        self.imageUrl = imageUrl
        self.source = source

    def to_json(self):
        ordered_data = {
            "name": self.name,
            "description": self.description,
            "servings": self.servings,
            "imageUrl": self.imageUrl,
            "prepTime": self.prepTime,
            "cookTime": self.cookTime,
            "ingredients": self.ingredients,
            "directions": self.instructionsList,
            "sources": self.source
        }
        return json.dumps(ordered_data, sort_keys=False, indent=4)


def parse_duration(duration):
    if duration.startswith('PT'):
        hours = 0
        minutes = 0
        if 'H' in duration:
            hours = int(duration.split('H')[0].replace('PT', ''))
            minutes_part = duration.split('H')[1]
        else:
            minutes_part = duration.replace('PT', '')

        if 'M' in minutes_part:
            minutes = int(minutes_part.replace('M', ''))

        if hours > 0:
            return f"{hours} h {minutes} m"
        else:
            return f"{minutes} m"
    return "No time available"


@app.route('/recipe')
def recipe_api():
    url = request.args.get('url')

    if url:
        return get_recipe_from_url(url)
    else:
        return jsonify({"error": "No URL provided"}), 400


def get_recipe_from_url(url):
    domain = urlparse(url).netloc
    if 'tasty.co' in domain:
        return fetch_tasty_recipe(url)
    elif 'resepichenom.com' in domain:
        return fetch_chenom_recipe(url)
    elif 'kingarthurbaking.com' in domain:
        print('executed foodie crush addiction')
        return fetch_kingarthurbaking_recipe(url)
    else:
        print('executed default recipe')
        return fetch_default_recipe(url)


def fetch_tasty_recipe(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    script = soup.find('script', type='application/ld+json')
    if script:
        json_text = script.string.replace('\n', ' ').replace('\r', ' ')
        try:
            data_list = json.loads(json_text)
        except json.decoder.JSONDecodeError as e:
            return jsonify({"error": f"Error decoding JSON: {str(e)}"}), 500

        if isinstance(data_list, list):
            data = next(
                (item for item in data_list if item.get('@type') == 'Recipe'), {})
        else:
            data = data_list

        if not data:
            return jsonify({"error": "No recipe data found"}), 404

        name = data.get('name', 'No name available')
        description = data.get('description', 'No description available')
        prep_time = parse_duration(
            data.get('prepTime', 'No prep time available'))
        cook_time = parse_duration(
            data.get('cookTime', 'No cook time available'))
        servings = data.get('recipeYield', 'No yield available')

        # Handle image data
        image_data = data.get('image', {})
        if isinstance(image_data, list) and len(image_data) > 0:
            image_url = image_data[0].get('url', 'No image available')
        elif isinstance(image_data, dict):
            image_url = image_data.get('url', 'No image available')
        elif isinstance(image_data, str):
            image_url = image_data
        else:
            image_url = 'No image available'

        ingredients_list = data.get('recipeIngredient', [])
        ingredients = []
        for ingredient in ingredients_list:
            if isinstance(ingredient, str):
                ingredients.append(ingredient.strip())

        instructions_data = data.get('recipeInstructions', [])
        instructions_list = []
        if isinstance(instructions_data, list):
            for step in instructions_data:
                if isinstance(step, dict) and 'text' in step:
                    instructions_list.append(step['text'].strip())
                elif isinstance(step, str):
                    instructions_list.append(step.strip())
        else:
            # assume it's a string or another simple structure
            instructions_list = [instructions_data]

        recipe = Recipe(name, description, prep_time, cook_time, servings,
                        ingredients, instructions_list, image_url, response.url)
        return recipe.to_json()
    else:
        return jsonify({"error": "No recipe data found"}), 404


def fetch_chenom_recipe(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    script = soup.find('script', type='application/ld+json')
    if script:
        json_text = script.string.replace('\n', ' ').replace('\r', ' ')
        try:
            data_list = json.loads(json_text)
        except json.decoder.JSONDecodeError as e:
            return jsonify({"error": f"Error decoding JSON: {str(e)}"}), 500

        if isinstance(data_list, list):
            data = next(
                (item for item in data_list if item.get('@type') == 'Recipe'), {})
        else:
            data = data_list

        if not data:
            return jsonify({"error": "No recipe data found"}), 404

        name = data.get('name', 'No name available')
        description = data.get('description', 'No description available')
        prep_time = parse_duration(
            data.get('prepTime', 'No prep time available'))
        cook_time = parse_duration(
            data.get('cookTime', 'No cook time available'))
        servings = data.get('recipeYield', 'No yield available')

        # Handle image data
        image_data = data.get('image', {})
        if isinstance(image_data, list) and len(image_data) > 0:
            image_url = image_data[0].get('url', 'No image available')
        elif isinstance(image_data, dict):
            image_url = image_data.get('url', 'No image available')
        elif isinstance(image_data, str):
            image_url = image_data
        else:
            image_url = 'No image available'

        ingredients_list = data.get('recipeIngredient', [])
        ingredients = []
        if isinstance(ingredients_list, list):
            for ingredient in ingredients_list:
                if isinstance(ingredient, str):
                    # Split the ingredients string by commas and strip any extra whitespace
                    ingredients.extend(
                        [ing.strip() for ing in ingredient.split(',') if ing.strip()])
                elif isinstance(ingredient, dict):
                    # Split the ingredients from the dict and strip any extra whitespace
                    ingredients.extend([ing.strip() for ing in ingredient.get(
                        'ingredient', '').split(',') if ing.strip()])
        else:
            ingredients.extend(
                [ing.strip() for ing in ingredients_list.split(',') if ing.strip()])

        # for ingredient in ingredients_list:
        #     if isinstance(ingredient, dict):
        #         ingredients.append(
        #             {'ingredient': ingredient.get('ingredient', '').strip()})
        #     elif isinstance(ingredient, str):
        #         ingredients.append({'ingredient': ingredient.strip()})

        instructions_data = data.get('recipeInstructions', [])
        instructions_list = []
        if isinstance(instructions_data, list):
            for step in instructions_data:
                if isinstance(step, dict) and 'text' in step:
                    instructions_list.append(step['text'].strip())
                elif isinstance(step, str):
                    instructions_list.append(step.strip())
        else:
            # assume it's a string or another simple structure
            instructions_list = [instructions_data]

        recipe = Recipe(name, description, prep_time, cook_time, servings,
                        ingredients, instructions_list, image_url, response.url)
        return recipe.to_json()
    else:
        return jsonify({"error": "No recipe data found"}), 404


def fetch_kingarthurbaking_recipe(url):
    driver = webdriver.Chrome()
    try:
        driver.get(url)  # Load the URL in the browser
        # Get the page source after JavaScript has been executed
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        script = soup.find('script', type='application/ld+json')
        if script:
            json_text = script.string.strip()
            data_list = json.loads(json_text)
            # Find the recipe in the graph
            if isinstance(data_list, dict) and '@graph' in data_list:
                data = next(
                    (item for item in data_list['@graph'] if item.get('@type') == 'Recipe'), None)
            else:
                data = data_list if isinstance(data_list, dict) and data_list.get(
                    '@type') == 'Recipe' else None

            if not data:
                return jsonify({"error": "No recipe data found"}), 404

            # Extract information
            name = data.get('name', 'No name available')
            description = data.get('description', 'No description available')
            if 'recipeYield' in data and isinstance(data['recipeYield'], list) and len(data['recipeYield']) > 0:
                # Get the first element of the list
                servings = data['recipeYield'][0]
            else:
                # Default message if 'recipeYield' is not a list or is empty
                servings = 'No yield available'
            prep_time = data.get('prepTime', 'No prep time available')
            cook_time = data.get('cookTime', 'No cook time available')
            image_url = data.get('image', {}).get('url', 'No image available')
            ingredients = data.get('recipeIngredient', [])

            instructions_data = data.get('recipeInstructions', [])
            instructions_list = []
            if isinstance(instructions_data, list):
                for step in instructions_data:
                    if isinstance(step, dict) and 'text' in step:
                        instructions_list.append(step['text'].strip())
                    elif isinstance(step, str):
                        instructions_list.append(step.strip())
            else:
                # assume it's a string or another simple structure
                instructions_list = [instructions_data]

            recipe = Recipe(name, description, prep_time, cook_time, servings,
                            ingredients, instructions_list, image_url, driver.current_url)
            return recipe.to_json()
        else:
            return jsonify({"error": "No recipe data found"}), 404
    finally:
        driver.quit()  # Properly close the WebDriver


def fetch_default_recipe(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    script = soup.find('script', type='application/ld+json')
    if script:
        json_text = script.string.replace('\n', ' ').replace('\r', ' ')
        try:
            data_list = json.loads(json_text)
        except json.decoder.JSONDecodeError as e:
            return jsonify({"error": f"Error decoding JSON: {str(e)}"}), 500

        if isinstance(data_list, list):
            data = next(
                (item for item in data_list if item.get('@type') == 'Recipe'), {})
        else:
            data = data_list

        if not data:
            return jsonify({"error": "No recipe data found"}), 404

        name = data.get('name', 'No name available')
        description = data.get('description', 'No description available')
        prep_time = parse_duration(
            data.get('prepTime', 'No prep time available'))
        cook_time = parse_duration(
            data.get('cookTime', 'No cook time available'))
        servings = data.get('recipeYield', 'No yield available')

        # Handle image data
        image_data = data.get('image', {})
        if isinstance(image_data, list) and len(image_data) > 0:
            image_url = image_data[0].get('url', 'No image available')
        elif isinstance(image_data, dict):
            image_url = image_data.get('url', 'No image available')
        elif isinstance(image_data, str):
            image_url = image_data
        else:
            image_url = 'No image available'

        ingredients_list = data.get('recipeIngredient', [])
        ingredients = []
        if isinstance(ingredients_list, list):
            for ingredient in ingredients_list:
                if isinstance(ingredient, str):
                    # Split the ingredients string by commas and strip any extra whitespace
                    ingredients.extend(
                        [ing.strip() for ing in ingredient.split(',') if ing.strip()])
                elif isinstance(ingredient, dict):
                    # Split the ingredients from the dict and strip any extra whitespace
                    ingredients.extend([ing.strip() for ing in ingredient.get(
                        'ingredient', '').split(',') if ing.strip()])
                else:
                    ingredients.extend(
                        [ing.strip() for ing in ingredients_list.split(',') if ing.strip()])

        instructions_data = data.get('recipeInstructions', [])
        instructions_list = []
        if isinstance(instructions_data, list):
            for step in instructions_data:
                if isinstance(step, dict) and 'text' in step:
                    instructions_list.append(step['text'].strip())
                elif isinstance(step, str):
                    instructions_list.append(step.strip())
        else:
            # assume it's a string or another simple structure
            instructions_list = [instructions_data]

        recipe = Recipe(name, description, prep_time, cook_time, servings,
                        ingredients, instructions_list, image_url, response.url)
        return recipe.to_json()
    else:
        return jsonify({"error": "No recipe data found"}), 404


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8000, debug=True)
