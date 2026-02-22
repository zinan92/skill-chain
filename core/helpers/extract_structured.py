"""Extract structured_output from claude CLI JSON envelope.

Usage: claude -p ... --output-format json --json-schema '...' | python3 extract_structured.py
"""
import sys
import json

try:
    envelope = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(json.dumps({"error": f"Failed to parse claude CLI envelope: {e}"}), file=sys.stdout)
    sys.exit(1)

if isinstance(envelope, dict):
    if envelope.get("is_error"):
        print(json.dumps({
            "error": "claude CLI reported error",
            "details": envelope.get("result", "unknown")
        }))
        sys.exit(1)

    structured = envelope.get("structured_output")
    if structured is not None:
        print(json.dumps(structured))
        sys.exit(0)

    result = envelope.get("result", "")
    if isinstance(result, str):
        cleaned = result.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines[1:] if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()
        try:
            parsed = json.loads(cleaned)
            print(json.dumps(parsed))
            sys.exit(0)
        except json.JSONDecodeError:
            pass

    print(json.dumps({"raw_result": result}))
else:
    print(json.dumps({"error": "unexpected envelope type", "data": str(envelope)}))
    sys.exit(1)
