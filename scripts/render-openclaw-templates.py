#!/usr/bin/env python3
"""
render-openclaw-templates.py — Render OpenClaw template files with variable substitution + overlay merge.

Usage:
  python3 render-openclaw-templates.py [--dry-run] [--output-dir PATH]

Behavior:
  1. Reads adapters/openclaw/*.template.md
  2. Substitutes ${VAR} placeholders from environment / .env
  3. If my/openclaw/FILE.md exists, uses it as override (overlay wins)
  4. Writes rendered files to --output-dir (default: stdout preview)
"""

import os
import re
import sys
from pathlib import Path


def load_env_file(env_path: Path) -> dict:
    """Load .env file into dict."""
    env = {}
    if not env_path.exists():
        return env
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            env[key] = value
    return env


def render_template(content: str, variables: dict) -> str:
    """Replace ${VAR} and ${VAR:-default} placeholders."""
    def replacer(match):
        var_expr = match.group(1)
        if ':-' in var_expr:
            var_name, _, default = var_expr.partition(':-')
            return variables.get(var_name, default)
        return variables.get(var_expr, match.group(0))

    return re.sub(r'\$\{([^}]+)\}', replacer, content)


def main():
    dry_run = '--dry-run' in sys.argv
    output_dir = None
    for i, arg in enumerate(sys.argv):
        if arg == '--output-dir' and i + 1 < len(sys.argv):
            output_dir = Path(sys.argv[i + 1])

    sco_home = Path(os.environ.get('SCO_HOME', Path(__file__).resolve().parent.parent))
    templates_dir = sco_home / 'adapters' / 'openclaw'
    overlay_dir = sco_home / 'my' / 'openclaw'
    env_file = sco_home / '.env'

    # Build variable map
    variables = {
        'SCO_HOME': str(sco_home),
        'HOME': str(Path.home()),
        'TARGET_REPO': os.environ.get('TARGET_REPO', '${TARGET_REPO}'),
        'AGENT_NAME': os.environ.get('AGENT_NAME', 'assistant'),
        'AGENT_ROLE': os.environ.get('AGENT_ROLE', 'development assistant'),
        'AGENT_DISPLAY_NAME': os.environ.get('AGENT_DISPLAY_NAME', 'Skill Chain Agent'),
        'USER_LANGUAGE': os.environ.get('USER_LANGUAGE', 'English'),
        'TECH_STACK': os.environ.get('TECH_STACK', 'not specified'),
    }

    # Load .env overrides
    env_vars = load_env_file(env_file)
    variables.update(env_vars)

    # Also pull from actual environment
    for key in variables:
        env_val = os.environ.get(key)
        if env_val:
            variables[key] = env_val

    print(f"SCO_HOME: {sco_home}")
    print(f"Templates: {templates_dir}")
    print(f"Overlays: {overlay_dir}")
    print()

    # Process each template
    template_files = sorted(templates_dir.glob('*.template.md'))

    if not template_files:
        print("No template files found!")
        sys.exit(1)

    for tmpl_path in template_files:
        # Derive output filename: AGENTS.template.md -> AGENTS.md
        out_name = tmpl_path.name.replace('.template.md', '.md')
        overlay_path = overlay_dir / out_name

        if overlay_path.exists():
            print(f"[OVERLAY] {out_name} <- my/openclaw/{out_name}")
            content = overlay_path.read_text()
        else:
            print(f"[RENDER] {out_name} <- {tmpl_path.name}")
            raw = tmpl_path.read_text()
            content = render_template(raw, variables)

        if dry_run:
            print(f"  --- Preview ({out_name}) ---")
            for line in content.splitlines()[:10]:
                print(f"  | {line}")
            if len(content.splitlines()) > 10:
                print(f"  | ... ({len(content.splitlines())} lines total)")
            print()
        elif output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / out_name).write_text(content)
            print(f"  -> {output_dir / out_name}")
        else:
            print(f"  (use --output-dir to write files)")

    if not dry_run and not output_dir:
        print()
        print("Hint: Use --output-dir PATH to write rendered files")
        print("      Use --dry-run to preview without writing")


if __name__ == '__main__':
    main()
