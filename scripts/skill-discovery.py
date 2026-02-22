#!/usr/bin/env python3
"""
skill-discovery.py — Scan SKILL.md files, validate frontmatter, and sync manifest.

Usage:
    python3 skill-discovery.py --check   # Compare manifest vs disk, report issues
    python3 skill-discovery.py --sync    # Update manifest for optional skills (dry-run for required/transitive)
"""

import json
import os
import re
import sys
from pathlib import Path

# Compatible with Python 3.8+ (no typing.TypedDict, no match statement)
REQUIRED_FIELDS = ("name", "description")
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_yaml_frontmatter(text):
    """Parse simple YAML frontmatter (key: value pairs only, no nested structures).

    Returns a dict of parsed fields, or None if no frontmatter found.
    Handles quoted and unquoted values.
    """
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return None

    fields = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        colon_idx = line.find(":")
        if colon_idx < 0:
            continue
        key = line[:colon_idx].strip()
        value = line[colon_idx + 1:].strip()
        # Strip surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        fields[key] = value

    return fields


def load_manifest(repo_root):
    """Load and return the skills-manifest.json as a dict."""
    manifest_path = repo_root / "manifest" / "skills-manifest.json"
    if not manifest_path.exists():
        print("ERROR: manifest/skills-manifest.json not found", file=sys.stderr)
        sys.exit(2)
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def get_manifest_skills(manifest):
    """Return a dict mapping skill_name -> category_name from the manifest."""
    result = {}
    for cat_name, cat_data in manifest.get("categories", {}).items():
        for skill in cat_data.get("skills", []):
            result[skill] = cat_name
    return result


def discover_skills_on_disk(skills_dir):
    """Scan skills/ directory. Return dict mapping skill_name -> frontmatter dict (or None)."""
    discovered = {}
    if not skills_dir.is_dir():
        return discovered

    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        skill_md = entry / "SKILL.md"
        if skill_md.exists():
            try:
                text = skill_md.read_text(encoding="utf-8", errors="replace")
                frontmatter = parse_yaml_frontmatter(text)
            except Exception:
                frontmatter = None
            discovered[entry.name] = frontmatter
        else:
            discovered[entry.name] = None

    return discovered


def check_mode(repo_root):
    """Compare manifest vs disk. Report issues. Return exit code."""
    manifest = load_manifest(repo_root)
    manifest_skills = get_manifest_skills(manifest)
    skills_dir = repo_root / "skills"
    disk_skills = discover_skills_on_disk(skills_dir)

    issues = []

    # Skills in manifest but missing on disk
    for skill, category in sorted(manifest_skills.items()):
        if skill not in disk_skills:
            issues.append(
                "MISSING_ON_DISK: '{}' listed in manifest ({}) but not found in skills/".format(
                    skill, category
                )
            )

    # Skills on disk but missing from manifest
    for skill in sorted(disk_skills.keys()):
        if skill not in manifest_skills:
            issues.append(
                "NOT_IN_MANIFEST: '{}' found in skills/ but not listed in manifest".format(skill)
            )

    # Frontmatter validation for all skills on disk
    for skill, frontmatter in sorted(disk_skills.items()):
        skill_md = skills_dir / skill / "SKILL.md"
        if not skill_md.exists():
            issues.append(
                "NO_SKILL_MD: '{}' directory exists but has no SKILL.md".format(skill)
            )
            continue
        if frontmatter is None:
            issues.append(
                "NO_FRONTMATTER: '{}' SKILL.md has no YAML frontmatter".format(skill)
            )
            continue
        for field in REQUIRED_FIELDS:
            if not frontmatter.get(field):
                issues.append(
                    "MISSING_FIELD: '{}' SKILL.md frontmatter missing required field '{}'".format(
                        skill, field
                    )
                )
        # Validate name matches directory
        fm_name = frontmatter.get("name", "")
        if fm_name and fm_name != skill:
            issues.append(
                "NAME_MISMATCH: '{}' SKILL.md frontmatter name is '{}' (expected '{}')".format(
                    skill, fm_name, skill
                )
            )

    # Report
    if not issues:
        manifest_count = len(manifest_skills)
        disk_count = len(disk_skills)
        print("OK: {} manifest skills, {} disk skills, all consistent".format(
            manifest_count, disk_count
        ))
        return 0

    print("Found {} issue(s):".format(len(issues)))
    for issue in issues:
        print("  - {}".format(issue))
    return 1


def sync_mode(repo_root):
    """Update manifest to match disk for optional skills. Dry-run for required/transitive."""
    manifest = load_manifest(repo_root)
    manifest_skills = get_manifest_skills(manifest)
    skills_dir = repo_root / "skills"
    disk_skills = discover_skills_on_disk(skills_dir)

    # Find skills on disk but not in manifest
    new_skills = sorted(set(disk_skills.keys()) - set(manifest_skills.keys()))
    # Find skills in manifest but not on disk
    removed_skills = sorted(set(manifest_skills.keys()) - set(disk_skills.keys()))

    changes_made = False
    manual_review = []

    # Handle removed skills
    for skill in removed_skills:
        category = manifest_skills[skill]
        if category == "optional":
            manifest["categories"]["optional"]["skills"].remove(skill)
            print("REMOVED: '{}' from optional (not on disk)".format(skill))
            changes_made = True
        else:
            manual_review.append(
                "WOULD_REMOVE: '{}' from {} (not on disk) — requires manual confirmation".format(
                    skill, category
                )
            )

    # Handle new skills (add to optional by default)
    for skill in new_skills:
        frontmatter = disk_skills[skill]
        if frontmatter is None:
            print("SKIP: '{}' has no valid frontmatter, cannot add to manifest".format(skill))
            continue
        missing_fields = [f for f in REQUIRED_FIELDS if not frontmatter.get(f)]
        if missing_fields:
            print("SKIP: '{}' missing frontmatter fields: {}".format(
                skill, ", ".join(missing_fields)
            ))
            continue
        manifest["categories"]["optional"]["skills"].append(skill)
        manifest["categories"]["optional"]["skills"].sort()
        print("ADDED: '{}' to optional".format(skill))
        changes_made = True

    # Report manual review items
    if manual_review:
        print("\nRequires manual review (required/transitive changes):")
        for item in manual_review:
            print("  - {}".format(item))

    # Write manifest if changes were made
    if changes_made:
        manifest_path = repo_root / "manifest" / "skills-manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print("\nManifest updated: {}".format(manifest_path))
    elif not manual_review:
        print("No changes needed — manifest is in sync.")

    return 1 if manual_review else 0


def main():
    repo_root = Path(__file__).resolve().parent.parent

    if len(sys.argv) < 2 or sys.argv[1] not in ("--check", "--sync"):
        print("Usage: {} [--check | --sync]".format(sys.argv[0]))
        print("  --check  Compare manifest vs skills on disk")
        print("  --sync   Update manifest for optional skills (dry-run for required/transitive)")
        sys.exit(2)

    mode = sys.argv[1]
    if mode == "--check":
        sys.exit(check_mode(repo_root))
    elif mode == "--sync":
        sys.exit(sync_mode(repo_root))


if __name__ == "__main__":
    main()
