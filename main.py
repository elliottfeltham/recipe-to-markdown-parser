import requests
import html
import json
import os
import sys
from pathlib import Path
from bs4 import BeautifulSoup

RECIPES_FOLDER_PATH = Path(os.environ.get("RECIPE_OUTPUT_DIR", ".")).expanduser()

# URLs for testing purposes
test_url = "https://www.allrecipes.com/recipe/30522/unbelievable-chicken/"

def get_arguments():
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return None
        

# Add a find recipe function which normalizes the searching and reduces repeated code below
def find_recipe(obj):
    type_field = obj.get("@type")

    if type_field == None:
        return False
    
    # If @type is a string
    if isinstance(type_field, str):
        if type_field.lower() == "recipe":
            return True
        else:
            return False
    
    # If @type is a list
    if isinstance(type_field, list):
        for item in type_field:
            if str(item).lower() == "recipe":
                return True
            
        return False
    
    # If recipe is neither string or list
    return False
    


def parse_recipe_obj(obj, url):
    return {"title": obj.get("name").title(), 
            "servings": obj.get("recipeYield"), 
            "ingredients": obj.get("recipeIngredient"), 
            "steps": obj.get("recipeInstructions"),
            "source": url}

def extract_recipe(url: str):
    # Send requests to recipe website
    response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    # Recipe webpage string
    recipe_webpage = response.text

    # Use the Beautiful Soup library to parse the HTML and find the recipe scripts
    soup = BeautifulSoup(recipe_webpage, 'html.parser')
    scripts = soup.find_all("script", {"type": "application/ld+json"})

    for tag in scripts:
        # Turn the JSON text in a dict or a list with error handling
        try:
            data = json.loads(html.unescape(tag.get_text() or ""))
        except json.JSONDecodeError:
            continue

        
        # Find the correct recipe script
        if isinstance(data, list):
            for obj in data:
                # Check if the "Recipe" type is in a string or a list
                if find_recipe(obj):
                        return parse_recipe_obj(obj, url)
                

        # Handle cases where the recipe uses the @graph schema
        elif isinstance(data, dict) and data.get("@graph"):
            for obj in data["@graph"]:
                if find_recipe(obj):
                    return parse_recipe_obj(obj, url)
        
                
        # Handle the simple dict JSON-LD
        else:
            if find_recipe(data):
                return parse_recipe_obj(data, url)
            
            
    # Return None if nothing found
    return None

                
# Format recipe function
def format_recipe_to_markdown(recipe: dict):
    ingredients = []
    for ingredient in recipe["ingredients"]:
        ingredients.append(f"+ {ingredient} \n")

    # Check if each step is in a dict or just a string
    steps = []

    if isinstance(recipe["steps"], str):
        steps.append(recipe["steps"])
    else:
        for step in recipe["steps"]:
            if isinstance(step, dict): 
                steps.append(step.get("text"))
            else:
                steps.append(step)

    method = []
    for index, step in enumerate(steps, start=1):
        method.append(f"{index}. {step}\n\n")

    RECIPES_FOLDER_PATH.mkdir(parents=True, exist_ok=True)
    filename = "".join(
        character for character in recipe["title"] if character not in '<>:"/\\|?*'
    ).strip()
    output_path = RECIPES_FOLDER_PATH / f"{filename or 'recipe'}.md"

    with output_path.open("w", encoding="utf-8") as file:
        # For my own obsidian tagging system
        file.write("> [!tags]- tags:\n")

        # Write recipe in markdown
        file.write(f"\n*Serves: {recipe["servings"]} people*\n\n"
                    "## Ingredients:\n\n")
        file.writelines(ingredients)
        file.write(f"\n\n" 
                    "## Method:\n\n")
        file.writelines(method)
        file.write(f"\n\n" 
                    f"[Visit the website]({recipe["source"]})")
        
def main():
    
    # Get the URL from the user and extract the webpage information
    cli_input = get_arguments()
    if cli_input:
        recipe_url = cli_input
    else:
        recipe_url = input("Paste a recipe's URL to send it to your notes: ").strip()

     
    recipe = extract_recipe(recipe_url)

    # Print a message if recipe not extracted
    if not recipe:
        print("No recipe found on that page.")
        return
    get_arguments()
    # Format recipe and write it to notes
    format_recipe_to_markdown(recipe)
    print(f"Successfully saved to {RECIPES_FOLDER_PATH.resolve()}!")


if __name__ == "__main__":
    main()
