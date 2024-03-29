from __future__ import annotations

from pathlib import Path

from quart import Quart, render_template_string, abort
from markdown import markdown as render_md
from watchfiles import awatch, Change

MARKDOWN_DIR = Path("./")

app = Quart(__name__)
markdowns = {}

for file in MARKDOWN_DIR.glob("*.md"):
    with open(file) as f:
        markdowns[file.name.removesuffix(".md")] = render_md(f.read())


async def hot_reload():
    async for changes in awatch(MARKDOWN_DIR):
        for change, file in changes:
            app.logger.debug("Detect file change in {file}.")

            file = Path(file)

            if file.suffix != ".md":
                continue

            if change == Change.deleted and file.parent.samefile(MARKDOWN_DIR):
                del markdowns[file.name.removesuffix(".md")]
                continue

            with open(file) as f:
                markdowns[file.name.removesuffix(".md")] = render_md(f.read())


@app.before_serving
async def startup():
    app.add_background_task(hot_reload)


@app.get('/')
async def index():
    names = list(markdowns.keys())

    template = """
    <html lang="en">
    <head>
        <title>Markdown Server</title>
    </head>
    </body>
        {% if names %}
        <ul>
            {% for name in names %}
                <li><a href="{{ name }}.html">{{ name }}</a></li>
            {% endfor %}
        </ul>
        {% else %}
        <p>No Markdown Files!</p>
        {% endif %}
    </body>
    """

    return await render_template_string(template, names=names)


@app.get('/<name>')
async def read_md(name):
    name = name.removesuffix(".html")
    md = markdowns.get(name, None)
    if not md:
        abort(404)

    return md


def run():
    app.run()
