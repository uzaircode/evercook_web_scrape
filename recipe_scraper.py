from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

app = Flask(__name__)


class Recipe:
    def __init__(self, title, description, prepTime, cookTime, servings, ingredients, instructionsList, imageUrl):
        self.title = title
        self.description = description
        self.prepTime = prepTime
        self.cookTime = cookTime
        self.servings = servings
        self.ingredients = ingredients
        self.instructionsList = instructionsList
        self.imageUrl = imageUrl

    def to_json(self):
        ordered_data = {
            "title": self.title,
            "description": self.description,
            "servings": self.servings,
            "imageUrl": self.imageUrl,
            "prepTime": self.prepTime,
            "cookTime": self.cookTime,
            "ingredients": self.ingredients,
            "instructionsList": self.instructionsList
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
    else:
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

        title = data.get('name', 'No title available')
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
        # for ingredient in ingredients_list.split(','):
        #     if isinstance(ingredient, dict):
        #         ingredients.append(
        #             {'ingredient': ingredient.get('ingredient', '').strip()})
        #     elif isinstance(ingredient, str):
        #         ingredients.append({'ingredient': ingredient.strip()})

        for ingredient in ingredients_list:
            if isinstance(ingredient, dict):
                ingredients.append(
                    {'ingredient': ingredient.get('ingredient', '').strip()})
            elif isinstance(ingredient, str):
                ingredients.append({'ingredient': ingredient.strip()})

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

        recipe = Recipe(title, description, prep_time, cook_time, servings,
                        ingredients, instructions_list, image_url)
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

        title = data.get('name', 'No title available')
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
        for ingredient in ingredients_list.split(','):
            if isinstance(ingredient, dict):
                ingredients.append(
                    {'ingredient': ingredient.get('ingredient', '').strip()})
            elif isinstance(ingredient, str):
                ingredients.append({'ingredient': ingredient.strip()})

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

        recipe = Recipe(title, description, prep_time, cook_time, servings,
                        ingredients, instructions_list, image_url)
        return recipe.to_json()
    else:
        return jsonify({"error": "No recipe data found"}), 404


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

        title = data.get('name', 'No title available')
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
        # for ingredient in ingredients_list.split(','):
        #     if isinstance(ingredient, dict):
        #         ingredients.append(
        #             {'ingredient': ingredient.get('ingredient', '').strip()})
        #     elif isinstance(ingredient, str):
        #         ingredients.append({'ingredient': ingredient.strip()})

        for ingredient in ingredients_list:
            if isinstance(ingredient, dict):
                ingredients.append(
                    {'ingredient': ingredient.get('ingredient', '').strip()})
            elif isinstance(ingredient, str):
                ingredients.append({'ingredient': ingredient.strip()})

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

        recipe = Recipe(title, description, prep_time, cook_time, servings,
                        ingredients, instructions_list, image_url)
        return recipe.to_json()
    else:
        return jsonify({"error": "No recipe data found"}), 404


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8000, debug=True)
