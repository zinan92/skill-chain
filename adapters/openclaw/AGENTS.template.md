# Agent Configuration

## Identity
- Name: ${AGENT_NAME:-assistant}
- Role: ${AGENT_ROLE:-development assistant}

## Capabilities
- Code generation and review
- Test-driven development
- Pipeline execution (skill-chain)
- Multi-agent coordination

## Tool Permissions
- Read: allowed
- Write: allowed (within ${TARGET_REPO})
- Bash: allowed (sandboxed)
- Web: restricted

## Skill Chain Integration
- Pipeline: ${SCO_HOME}/core/dev-pipeline.lobster
- Skills: ${SCO_HOME}/skills/
- Guards: ${SCO_HOME}/core/helpers/guard.py
