import tempfile
import unittest
from pathlib import Path

from main import extract_recipe_from_html, recipe_to_markdown, safe_filename, save_recipe


RECIPE_HTML = """
<html><head><script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [{
    "@type": "Recipe",
    "name": "Lemon / Pasta",
    "recipeYield": "2",
    "recipeIngredient": ["200g pasta", "1 lemon"],
    "recipeInstructions": [
      {"@type": "HowToStep", "text": "Boil the pasta."},
      {"@type": "HowToStep", "text": "Add the lemon."}
    ]
  }]
}
</script></head></html>
"""


class RecipeParserTests(unittest.TestCase):
    def test_extracts_recipe_from_graph_json_ld(self):
        recipe = extract_recipe_from_html(RECIPE_HTML, "https://example.com/recipe")
        self.assertIsNotNone(recipe)
        assert recipe is not None
        self.assertEqual(recipe["title"], "Lemon / Pasta")
        self.assertEqual(recipe["steps"], ["Boil the pasta.", "Add the lemon."])

    def test_formats_markdown_with_source(self):
        recipe = extract_recipe_from_html(RECIPE_HTML, "https://example.com/recipe")
        assert recipe is not None
        markdown = recipe_to_markdown(recipe)
        self.assertIn("# Lemon / Pasta", markdown)
        self.assertIn("- 200g pasta", markdown)
        self.assertIn("1. Boil the pasta.", markdown)
        self.assertIn("[Source](https://example.com/recipe)", markdown)

    def test_sanitises_output_filename(self):
        self.assertEqual(safe_filename("../Lemon / Pasta"), "Lemon Pasta.md")

    def test_saves_inside_selected_output_directory(self):
        recipe = extract_recipe_from_html(RECIPE_HTML, "https://example.com/recipe")
        assert recipe is not None
        with tempfile.TemporaryDirectory() as directory:
            path = save_recipe(recipe, Path(directory))
            self.assertEqual(path.parent, Path(directory))
            self.assertTrue(path.is_file())

    def test_ignores_malformed_json_ld(self):
        malformed = '<script type="application/ld+json">not-json</script>'
        self.assertIsNone(extract_recipe_from_html(malformed, "https://example.com"))


if __name__ == "__main__":
    unittest.main()
