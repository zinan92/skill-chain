# Customization Guide

## Replace a Skill

1. Create your custom skill in `skills/<name>/SKILL.md`
2. Follow the same input/output schema
3. Re-run install to update symlinks

## Add a Guard Check

Edit `core/helpers/guard.py` to add validation logic:
- Each `--check <name>` maps to a validation function
- Guards receive structured JSON on stdin
- Guards exit 0 (pass) or 1 (fail)

## Modify Pipeline Steps

Edit `core/dev-pipeline.lobster`:
- Add new steps with unique `id`
- Chain via `stdin: $previous_step.stdout`
- Add guard calls as needed

## Add New Rules

Place rule files in `rules/{common,python,typescript}/`:
- Rules are `.md` files loaded by Claude Code
- Follow existing naming conventions
- Re-run install to link new rules

## Custom OpenClaw Templates

1. Edit templates in `adapters/openclaw/*.template.md`
2. Use `${VAR}` placeholders
3. Personal overrides go in `my/openclaw/`

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| SCO_HOME | skill-chain root | ~/skill-chain |
| TARGET_REPO | Project to run pipeline on | (required per-run) |
| CLAUDE_MODEL | Override Claude model | claude-sonnet-4-5 |
