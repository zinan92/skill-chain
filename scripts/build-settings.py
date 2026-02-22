#!/usr/bin/env python3
"""
build-settings.py — Merge skill-chain settings template into user's Claude Code settings.

Usage:
  python3 build-settings.py [--dry-run] [--output PATH]

Behavior:
  1. Reads adapters/claude-code/settings.json.tmpl
  2. Renders template variables (SCO_HOME, etc.)
  3. Reads user's existing ~/.claude/settings.json (if exists)
  4. Deep-merges (skill-chain additions only, never overwrites user keys)
  5. Writes merged result to --output or prints to stdout
"""

import json
import os
import sys
from copy import deepcopy
from pathlib import Path


def get_sco_home() -> str:
    """Resolve SCO_HOME from env or default."""
    return os.environ.get('SCO_HOME', str(Path(__file__).resolve().parent.parent))


def render_template(template: dict, variables: dict) -> dict:
    """Recursively replace ${VAR} placeholders in a dict."""
    if isinstance(template, str):
        result = template
        for key, value in variables.items():
            result = result.replace(f'${{{key}}}', value)
        return result
    elif isinstance(template, dict):
        return {k: render_template(v, variables) for k, v in template.items()}
    elif isinstance(template, list):
        return [render_template(item, variables) for item in template]
    return template


def deep_merge(base: dict, overlay: dict) -> dict:
    """Deep merge overlay into base. Overlay values win for scalars, merge for dicts, append for lists."""
    result = deepcopy(base)
    for key, value in overlay.items():
        if key.startswith('_'):
            continue  # Skip meta keys like _comment
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                # For hooks, append without duplicating
                existing_descs = {item.get('description', '') for item in result[key] if isinstance(item, dict)}
                for item in value:
                    if isinstance(item, dict) and item.get('description', '') not in existing_descs:
                        result[key].append(item)
                    elif not isinstance(item, dict) and item not in result[key]:
                        result[key].append(item)
            # For scalar conflicts, keep user's existing value
        else:
            result[key] = deepcopy(value)
    return result


def main():
    dry_run = '--dry-run' in sys.argv
    output_path = None
    for i, arg in enumerate(sys.argv):
        if arg == '--output' and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]

    sco_home = get_sco_home()
    template_path = Path(sco_home) / 'adapters' / 'claude-code' / 'settings.json.tmpl'
    user_settings_path = Path.home() / '.claude' / 'settings.json'

    if not template_path.exists():
        print(f"ERROR: Template not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    # Load and render template
    template = json.loads(template_path.read_text())
    variables = {
        'SCO_HOME': sco_home,
        'HOME': str(Path.home()),
    }
    rendered = render_template(template, variables)

    # Load user settings
    user_settings = {}
    if user_settings_path.exists():
        user_settings = json.loads(user_settings_path.read_text())

    # Merge
    merged = deep_merge(user_settings, rendered)

    output = json.dumps(merged, indent=2, ensure_ascii=False)

    if dry_run:
        print("=== DRY RUN: Would produce the following settings ===")
        print(output)
        print(f"\n=== Would write to: {output_path or user_settings_path} ===")
    elif output_path:
        Path(output_path).write_text(output)
        print(f"Settings written to: {output_path}")
    else:
        print(output)


if __name__ == '__main__':
    main()
