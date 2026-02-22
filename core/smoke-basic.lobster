name: smoke-basic
description: "Test Lobster runtime basics without claude CLI dependency"

steps:
  - id: produce
    command: "echo '{\"status\": \"ok\", \"weight\": \"Medium\", \"files_changed\": [\"README.md\"]}'"

  - id: consume
    command: "python3 -c \"import sys,json; d=json.load(sys.stdin); print(json.dumps({'received': True, 'keys': sorted(d.keys()), 'weight': d['weight']}))\""
    stdin: $produce.stdout

  - id: gate
    command: "python3 -c \"import sys,json; d=json.load(sys.stdin); print(json.dumps({'prompt': 'Approve pipeline?', 'items': [{'weight': d['weight']}], 'requiresApproval': {'prompt': 'Continue?', 'items': []}}))\""
    stdin: $consume.stdout
    approval: required

  - id: final
    command: "python3 -c \"import sys; data=sys.stdin.read(); print(f'After approval, got: {data.strip()}')\""
    stdin: $consume.stdout
