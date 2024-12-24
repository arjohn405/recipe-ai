from flask import Flask, render_template, jsonify, url_for
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import base64
from PIL import Image
import requests
from io import BytesIO
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Gemini API Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

def generate_image_url(recipe_name):
    try:
        # Clean and prepare the recipe name for image search
        # Remove common words that might interfere with the search
        common_words = ['recipe', 'with', 'and', 'the', 'a', 'an', 'in', 'on', 'at', 'to']
        keywords = recipe_name.lower()
        for word in common_words:
            keywords = keywords.replace(word, '')
            
        # Add specific food-related terms
        keywords = keywords.strip().replace(' ', ',')
        search_terms = f"{keywords},food,dish,gourmet,homemade"
        
        # Add cache buster to get fresh image each time
        timestamp = int(time.time())
        
        # Construct URL with specific parameters
        return f"https://source.unsplash.com/featured/1200x800/?{search_terms}&t={timestamp}"
    except Exception as e:
        print(f"Image generation error: {e}")
        return f"https://source.unsplash.com/featured/1200x800/?cooking,food&t={int(time.time())}"

def get_recipe_from_gemini(prompt="Give me a random recipe with ingredients and instructions"):
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(f"""
        Please provide a recipe in the following JSON format without any additional text or markdown.
        Make sure the recipe name is specific and descriptive (e.g., "Creamy Garlic Parmesan Pasta" instead of just "Pasta"):
        {{
            "name": "Recipe Name",
            "description": "Brief description",
            "ingredients": ["ingredient 1", "ingredient 2"],
            "instructions": ["step 1", "step 2"],
            "prep_time": "XX minutes",
            "cook_time": "XX minutes",
            "servings": X,
            "category": "main dish/dessert/appetizer/etc"
        }}
        {prompt}
        """)
        
        text = response.text.strip()
        if text.startswith('```json'):
            text = text[7:-3]
        elif text.startswith('```'):
            text = text[3:-3]
        
        recipe_data = json.loads(text)
        
        # Generate image URL using both name and category
        search_terms = f"{recipe_data['name']},{recipe_data.get('category', 'food')}"
        recipe_data['image_url'] = generate_image_url(search_terms)
        
        return json.dumps(recipe_data)
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/recipe")
def get_recipe():
    recipe = get_recipe_from_gemini()
    if recipe:
        return jsonify({"success": True, "recipe": recipe})
    return jsonify({"success": False, "error": "Could not generate recipe"}), 500

if __name__ == "__main__":
    app.run(debug=True)
