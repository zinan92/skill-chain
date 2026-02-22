"""Extract review verdict from claude CLI envelope and format for Lobster approval.

Usage: claude -p @review.txt --output-format json --json-schema '...' | python3 extract_review.py
"""
import sys
import json

try:
    envelope = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(json.dumps({"error": f"Failed to parse envelope: {e}"}))
    sys.exit(1)

structured = envelope.get("structured_output", {})
if not structured:
    result = envelope.get("result", "")
    if isinstance(result, str):
        cleaned = result.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines[1:] if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()
        try:
            structured = json.loads(cleaned)
        except json.JSONDecodeError:
            structured = {}

verdict = structured.get("verdict", "unknown")
issues = structured.get("issues", [])
summary = structured.get("summary", "")

output = {
    "verdict": verdict,
    "issues": issues,
    "summary": summary,
    "requiresApproval": {
        "prompt": f"Review verdict: {verdict}. {summary}",
        "items": issues
    }
}

print(json.dumps(output))
