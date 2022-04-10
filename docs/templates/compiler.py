#!/usr/bin/env python3
# Compiles Jinja2 templates to MD files
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timezone
import json
import os


def timestamp():
    # Generate Timestamp
    utc_timestamp = datetime.now(timezone.utc).replace(
        microsecond=0)  # UTC time
    # timestamp in local timezone
    return utc_timestamp.astimezone()


def compile_to_html(template_path, output_path):
    root = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(root, '.')
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template(template_path)
    filename = os.path.join(root, output_path)
    with open(filename, 'w', encoding="utf-8") as fh:
        fh.write(template.render(
            GEN_DATETIME=timestamp(),
        ))


def driver():
    # Path relative to script path not pwd
    arguments = [
        {
            "template_path":    'README.md/base.md.j2',
            "output_path":      '../../README.md',
        },
    ]
    for arg in arguments:
        template_path = arg.get("template_path")
        output_path = arg.get("output_path")
        compile_to_html(
            template_path=template_path,
            output_path=output_path)
        print(f"{template_path} -> {output_path} compiled successfully...")


if __name__ == "__main__":
    driver()