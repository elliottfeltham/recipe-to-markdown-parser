# Recipe to Markdown Parser

A small Python CLI that extracts schema.org Recipe JSON-LD from a web page and
saves a portable Markdown recipe. It began as a practical way to move recipes
into Obsidian while learning HTML parsing and structured web data.

## Features

- Supports Recipe objects stored directly, in arrays, or inside `@graph`
- Handles string instructions, `HowToStep`, and nested instruction sections
- Writes to a user-selected directory rather than a machine-specific path
- Sanitises generated filenames and preserves the source URL
- Separates network retrieval, parsing, formatting, and file output for testing

## Installation

Requires Python 3.10 or later.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate with `.venv\\Scripts\\Activate.ps1`.

## Usage

```bash
python main.py "https://example.com/recipe" --output-dir ./recipes
```

The URL may be omitted to enter it interactively. The output directory defaults
to the current directory and can also be set with `RECIPE_OUTPUT_DIR`.

To inspect all JSON-LD blocks on a page while debugging:

```bash
python json-reader.py "https://example.com/recipe"
```

## Tests

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the test suite for pushes and pull requests to `main`.

## Limitations

- The parser intentionally targets schema.org Recipe JSON-LD rather than
  site-specific HTML.
- Websites that render structured data only after client-side JavaScript runs
  are not supported.
- Recipe publishers use inconsistent shapes, so incomplete objects are skipped.
- This is a learning-oriented CLI, not a general crawling service. Respect a
  site's terms, robots policy, and request limits.
- A production-focused extractor should use a mature project such as
  [recipe-scrapers](https://github.com/hhursev/recipe-scrapers).

## License

Released under the [MIT License](LICENSE).
