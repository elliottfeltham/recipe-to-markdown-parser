"""Extract schema.org Recipe JSON-LD and save it as Markdown."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


REQUEST_TIMEOUT_SECONDS = 10


def find_recipe(obj: Any) -> bool:
    """Return whether a JSON-LD object declares the Recipe type."""
    if not isinstance(obj, dict):
        return False
    type_field = obj.get("@type")
    if isinstance(type_field, str):
        return type_field.casefold() == "recipe"
    if isinstance(type_field, list):
        return any(str(item).casefold() == "recipe" for item in type_field)
    return False


def iter_json_ld_objects(data: Any) -> Iterable[dict[str, Any]]:
    """Yield objects from common top-level and @graph JSON-LD shapes."""
    if isinstance(data, list):
        for item in data:
            yield from iter_json_ld_objects(item)
    elif isinstance(data, dict):
        yield data
        graph = data.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                yield from iter_json_ld_objects(item)


def normalise_steps(value: Any) -> list[str]:
    """Flatten Recipe instructions and HowToSection entries into plain steps."""
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list):
        return []

    steps: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            steps.append(item.strip())
        elif isinstance(item, dict):
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                steps.append(text.strip())
            nested = item.get("itemListElement")
            if nested is not None:
                steps.extend(normalise_steps(nested))
    return steps


def parse_recipe_obj(obj: dict[str, Any], url: str) -> dict[str, Any] | None:
    title = obj.get("name")
    ingredients = obj.get("recipeIngredient")
    steps = normalise_steps(obj.get("recipeInstructions"))
    if not isinstance(title, str) or not title.strip():
        return None
    if not isinstance(ingredients, list) or not ingredients or not steps:
        return None

    return {
        "title": title.strip(),
        "servings": obj.get("recipeYield"),
        "ingredients": [str(item).strip() for item in ingredients if str(item).strip()],
        "steps": steps,
        "source": url,
    }


def extract_recipe_from_html(page_html: str, url: str) -> dict[str, Any] | None:
    """Extract the first complete Recipe object from an HTML document."""
    soup = BeautifulSoup(page_html, "html.parser")
    scripts = soup.find_all("script", {"type": "application/ld+json"})
    for tag in scripts:
        try:
            data = json.loads(html.unescape(tag.get_text() or ""))
        except (json.JSONDecodeError, TypeError):
            continue
        for obj in iter_json_ld_objects(data):
            if find_recipe(obj):
                recipe = parse_recipe_obj(obj, url)
                if recipe is not None:
                    return recipe
    return None


def extract_recipe(url: str) -> dict[str, Any] | None:
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("Recipe URL must use http or https.")

    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": "recipe-to-markdown-parser/1.0"},
    )
    response.raise_for_status()
    return extract_recipe_from_html(response.text, url)


def recipe_to_markdown(recipe: dict[str, Any]) -> str:
    servings = recipe.get("servings") or "Not specified"
    ingredients = "\n".join(f"- {item}" for item in recipe["ingredients"])
    steps = "\n\n".join(
        f"{index}. {step}" for index, step in enumerate(recipe["steps"], start=1)
    )
    return (
        f"# {recipe['title']}\n\n"
        f"*Serves: {servings}*\n\n"
        "## Ingredients\n\n"
        f"{ingredients}\n\n"
        "## Method\n\n"
        f"{steps}\n\n"
        f"[Source]({recipe['source']})\n"
    )


def safe_filename(title: str) -> str:
    name = re.sub(r"[^\w .-]", "", title, flags=re.UNICODE).strip(" .")
    name = re.sub(r"\s+", " ", name)
    return f"{name or 'recipe'}.md"


def save_recipe(recipe: dict[str, Any], output_directory: Path) -> Path:
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / safe_filename(recipe["title"])
    output_path.write_text(recipe_to_markdown(recipe), encoding="utf-8")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert schema.org Recipe JSON-LD into a Markdown file."
    )
    parser.add_argument("url", nargs="?", help="Recipe page URL")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(os.getenv("RECIPE_OUTPUT_DIR", ".")),
        help="Destination folder (default: RECIPE_OUTPUT_DIR or current folder)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    url = args.url or input("Paste a recipe URL: ").strip()
    try:
        recipe = extract_recipe(url)
    except (ValueError, requests.RequestException) as error:
        print(f"Could not fetch recipe: {error}")
        return 1

    if recipe is None:
        print("No complete schema.org Recipe data was found on that page.")
        return 1

    output_path = save_recipe(recipe, args.output_dir)
    print(f"Saved recipe to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
