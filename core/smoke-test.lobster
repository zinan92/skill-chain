name: smoke-test
description: "Validate Lobster runtime + claude CLI integration"

args:
  repo:
    required: true
    description: "Target repository path (absolute)"

steps:
  - id: probe
    command: >
      unset CLAUDECODE &&
      cd ${repo} &&
      claude -p 'Output status ok and weight Medium.'
      --output-format json
      --json-schema '{"type":"object","properties":{"status":{"type":"string"},"weight":{"type":"string","enum":["Light","Medium","Heavy"]},"files_changed":{"type":"array","items":{"type":"string"}}},"required":["status","weight"]}'
      --max-turns 5
      | python3 -c "import sys,json; envelope=json.load(sys.stdin); print(json.dumps(envelope.get('structured_output', {})))"

  - id: gate
    command: "python3 -c \"import sys,json; d=json.load(sys.stdin); print(json.dumps({'received': True, 'keys': sorted(d.keys()), 'weight': d.get('weight','MISSING'), 'requiresApproval': {'prompt': 'Data looks correct. Continue?', 'items': [d]}}))\""
    stdin: $probe.stdout
    approval: required

  - id: echo-back
    command: "python3 -c \"import sys,json; d=json.load(sys.stdin); print(json.dumps({'final': True, 'stdin_matches': d.get('weight') is not None, 'data': d}))\""
    stdin: $probe.stdout
