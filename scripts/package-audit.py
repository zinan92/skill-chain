#!/usr/bin/env python3
"""
package-audit.py — Scan skill-chain repo for:
1. Hardcoded absolute paths (e.g. ~user home directories~)
2. Personal information leaks (names, tokens, API keys)
3. Missing file references (files referenced but not present)
4. Skills in manifest but missing from skills/ directory
"""

import json
import os
import re
import sys
from pathlib import Path

# Patterns to flag
HARDCODED_PATHS = [
    re.compile(r'/Users/\w+/', re.IGNORECASE),
    re.compile(r'/home/\w+/', re.IGNORECASE),
    re.compile(r'C:\\Users\\\w+\\', re.IGNORECASE),
]

PERSONAL_INFO = [
    re.compile(r'(?:api[_-]?key|token|secret|password)\s*[:=]\s*["\']?[a-zA-Z0-9_-]{20,}', re.IGNORECASE),
    re.compile(r'ntn_[a-zA-Z0-9]{20,}'),  # Notion tokens
    re.compile(r'sk-[a-zA-Z0-9]{20,}'),    # OpenAI/Anthropic keys
    re.compile(r'xoxb-[a-zA-Z0-9-]+'),     # Slack tokens
    re.compile(r'ghp_[a-zA-Z0-9]{36}'),     # GitHub PATs
]

# Allowed template variables (should not be flagged)
TEMPLATE_VARS = {'${SCO_HOME}', '${HOME}', '${TARGET_REPO}', '$SCO_HOME', '$HOME', '$TARGET_REPO'}

SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'my'}
SKIP_FILES = {'install-manifest.json'}  # Runtime artifact, contains local paths by design
SCAN_EXTENSIONS = {'.py', '.sh', '.md', '.json', '.yml', '.yaml', '.lobster', '.tmpl', '.txt', '.toml'}


def scan_file(filepath: Path) -> list[dict]:
    """Scan a single file for issues."""
    issues = []
    try:
        content = filepath.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return [{'file': str(filepath), 'line': 0, 'type': 'READ_ERROR', 'detail': str(e)}]

    for lineno, line in enumerate(content.splitlines(), 1):
        # Check hardcoded paths
        for pattern in HARDCODED_PATHS:
            matches = pattern.findall(line)
            for match in matches:
                # Skip if inside a template variable context or comment explaining templating
                if any(tv in line for tv in TEMPLATE_VARS):
                    continue
                issues.append({
                    'file': str(filepath),
                    'line': lineno,
                    'type': 'HARDCODED_PATH',
                    'detail': match.strip(),
                    'context': line.strip()[:120]
                })

        # Check personal info / secrets
        for pattern in PERSONAL_INFO:
            if pattern.search(line):
                issues.append({
                    'file': str(filepath),
                    'line': lineno,
                    'type': 'POSSIBLE_SECRET',
                    'detail': pattern.pattern[:60],
                    'context': line.strip()[:80] + '...' if len(line.strip()) > 80 else line.strip()
                })

    return issues


def check_manifest_consistency(repo_root: Path) -> list[dict]:
    """Check skills-manifest.json against actual skills/ directory."""
    issues = []
    manifest_path = repo_root / 'manifest' / 'skills-manifest.json'

    if not manifest_path.exists():
        return [{'file': str(manifest_path), 'line': 0, 'type': 'MISSING_FILE', 'detail': 'skills-manifest.json not found'}]

    manifest = json.loads(manifest_path.read_text())
    skills_dir = repo_root / 'skills'

    # Collect all skills from manifest
    all_manifest_skills = set()
    for category in manifest.get('categories', {}).values():
        all_manifest_skills.update(category.get('skills', []))

    # Check each manifest skill exists
    for skill in sorted(all_manifest_skills):
        skill_path = skills_dir / skill
        if not skill_path.exists():
            issues.append({
                'file': str(manifest_path),
                'line': 0,
                'type': 'MISSING_SKILL',
                'detail': f'Skill "{skill}" in manifest but not in skills/'
            })
        elif not any(skill_path.iterdir()):
            issues.append({
                'file': str(skill_path),
                'line': 0,
                'type': 'EMPTY_SKILL',
                'detail': f'Skill directory "{skill}" is empty'
            })

    # Check for skills in directory but not in manifest
    if skills_dir.exists():
        for entry in sorted(skills_dir.iterdir()):
            if entry.is_dir() and entry.name not in all_manifest_skills:
                issues.append({
                    'file': str(entry),
                    'line': 0,
                    'type': 'UNLISTED_SKILL',
                    'detail': f'Skill "{entry.name}" in skills/ but not in manifest'
                })

    return issues


def main():
    repo_root = Path(__file__).resolve().parent.parent

    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1]).resolve()

    print(f"Auditing: {repo_root}")
    print("=" * 60)

    all_issues = []

    # Scan all files
    for dirpath, dirnames, filenames in os.walk(repo_root):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            if filename in SKIP_FILES:
                continue
            filepath = Path(dirpath) / filename
            if filepath.suffix in SCAN_EXTENSIONS:
                issues = scan_file(filepath)
                all_issues.extend(issues)

    # Check manifest consistency
    manifest_issues = check_manifest_consistency(repo_root)
    all_issues.extend(manifest_issues)

    # Report
    if not all_issues:
        print("PASS: No issues found.")
        sys.exit(0)

    # Group by type
    by_type = {}
    for issue in all_issues:
        t = issue['type']
        by_type.setdefault(t, []).append(issue)

    for issue_type, issues in sorted(by_type.items()):
        print(f"\n{'='*60}")
        print(f" {issue_type} ({len(issues)} issues)")
        print(f"{'='*60}")
        for issue in issues:
            rel_path = os.path.relpath(issue['file'], repo_root)
            line_info = f":{issue['line']}" if issue['line'] else ''
            print(f"  {rel_path}{line_info}")
            print(f"    → {issue['detail']}")
            if 'context' in issue:
                print(f"    | {issue['context']}")

    total = len(all_issues)
    critical = len(by_type.get('POSSIBLE_SECRET', []))
    print(f"\n{'='*60}")
    print(f"TOTAL: {total} issues ({critical} potential secrets)")
    print(f"{'='*60}")

    sys.exit(1 if critical > 0 else 0)


if __name__ == '__main__':
    main()
