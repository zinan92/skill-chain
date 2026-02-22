name: dev-pipeline
description: "Skill-chain pipeline with transition guards: triage → plan → implement → review → verify → commit"

args:
  repo:
    required: true
    description: "Target repository path (absolute)"
  task:
    description: "Task description to implement"

env:
  GUARD: "${SCO_HOME}/core/helpers/guard.py"
  EXTRACT: "${SCO_HOME}/core/helpers/extract_structured.py"
  EXTRACT_REVIEW: "${SCO_HOME}/core/helpers/extract_review.py"

steps:
  # Step 1: init — write task to temp file, clean previous workflow state
  - id: init
    command: "rm -rf /tmp/workflow && mkdir -p /tmp/workflow && python3 -c \"import sys,json; task=sys.stdin.read().strip(); open('/tmp/workflow/task.txt','w').write(task); print(json.dumps({'task':task,'repo':'${repo}'}))\""
    stdin: "${task}"

  # Step 2: /triage skill → guard(triage)
  - id: triage
    command: "unset CLAUDECODE && cd ${repo} && claude -p \"Use the /triage skill. Classify this task from stdin. Read the repo to assess scope.\" --output-format json --json-schema '{\"type\":\"object\",\"properties\":{\"type\":{\"type\":\"string\"},\"weight\":{\"type\":\"string\",\"enum\":[\"Light\",\"Medium\",\"Heavy\"]},\"summary\":{\"type\":\"string\"},\"affected_areas\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}},\"hard_signals\":{\"type\":\"object\",\"properties\":{\"lines_changed\":{\"type\":\"string\"},\"files_touched\":{\"type\":\"string\"},\"modules_crossed\":{\"type\":\"string\"}}},\"routing\":{\"type\":\"string\"}},\"required\":[\"type\",\"weight\",\"summary\",\"routing\"]}' --max-turns 20 --permission-mode bypassPermissions --add-dir ${repo} | python3 ${EXTRACT} | python3 ${GUARD} --check triage"
    stdin: $init.stdout

  # Step 3: route — Light skips plan, Medium/Heavy runs /writing-plans → guard(route)
  - id: route
    command: "python3 ${SCO_HOME}/core/helpers/router.py ${repo} | python3 ${GUARD} --check route"
    stdin: $triage.stdout

  # Step 4: /mvu-execution skill → guard(implement)
  - id: implement
    command: "unset CLAUDECODE && cd ${repo} && claude -p \"Use the /mvu-execution skill. You are the developer agent. Read the task context from stdin (includes triage and optional plan). Implement the changes following the MVU protocol: read code first, write tests first, implement minimal changes, self-review, then report.\" --output-format json --json-schema '{\"type\":\"object\",\"properties\":{\"summary\":{\"type\":\"string\"},\"type\":{\"type\":\"string\"},\"files_changed\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}},\"files_created\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}},\"tests_run\":{\"type\":\"boolean\"},\"tests_passed\":{\"type\":\"boolean\"},\"self_review\":{\"type\":\"string\"}},\"required\":[\"summary\",\"files_changed\",\"files_created\"]}' --max-turns 50 --permission-mode dontAsk --allowedTools 'Read,Glob,Grep,Edit,Write,Bash' --add-dir ${repo} | python3 ${EXTRACT} | python3 ${GUARD} --check implement"
    stdin: $route.stdout

  # Step 5: /requesting-code-review skill → guard(review) → approval gate
  - id: review
    command: "unset CLAUDECODE && cd ${repo} && claude -p \"Use the /requesting-code-review skill. You are the code reviewer. Read the implementation report from stdin, then read every changed file. Check spec compliance AND code quality. Produce a verdict.\" --output-format json --json-schema '{\"type\":\"object\",\"properties\":{\"verdict\":{\"type\":\"string\",\"enum\":[\"approved\",\"with_fixes\",\"rejected\"]},\"spec_compliance\":{\"type\":\"string\"},\"code_quality\":{\"type\":\"string\"},\"issues\":{\"type\":\"array\",\"items\":{\"type\":\"object\",\"properties\":{\"severity\":{\"type\":\"string\",\"enum\":[\"critical\",\"high\",\"medium\",\"low\"]},\"file\":{\"type\":\"string\"},\"line\":{\"type\":\"integer\"},\"description\":{\"type\":\"string\"}},\"required\":[\"severity\",\"description\"]}},\"summary\":{\"type\":\"string\"}},\"required\":[\"verdict\",\"summary\"]}' --max-turns 30 --permission-mode bypassPermissions --add-dir ${repo} | python3 ${EXTRACT_REVIEW} | python3 ${GUARD} --check review"
    stdin: $implement.stdout
    approval: required

  # Step 6: /verification-before-completion skill → guard(verify)
  - id: verify
    command: "unset CLAUDECODE && cd ${repo} && claude -p \"Use the /verification-before-completion skill. Run fresh tests and verify the implementation actually works. No claims without evidence.\" --output-format json --json-schema '{\"type\":\"object\",\"properties\":{\"tests_command\":{\"type\":\"string\"},\"tests_output\":{\"type\":\"string\"},\"tests_passed\":{\"type\":\"boolean\"},\"evidence\":{\"type\":\"string\"},\"verified\":{\"type\":\"boolean\"}},\"required\":[\"verified\",\"evidence\"]}' --max-turns 15 --permission-mode dontAsk --allowedTools 'Read,Glob,Grep,Bash' --add-dir ${repo} | python3 ${EXTRACT} | python3 ${GUARD} --check verify"
    condition: $review.approved

  # Step 7: pre-commit guard — aggregate triple gate (review + verify + approval)
  - id: pre_commit
    command: "python3 ${GUARD} --check pre_commit"
    stdin: $implement.stdout
    condition: $review.approved

  # Step 8: commit — selective git add from guarded implementation report
  - id: commit
    command: "python3 ${SCO_HOME}/core/helpers/commit.py ${repo}"
    stdin: $pre_commit.stdout
    condition: $review.approved
