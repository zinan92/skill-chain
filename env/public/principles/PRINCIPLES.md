# Skill Chain Principles

## Core Development Principles

1. **Test First**: Write tests before implementation. No exceptions.
2. **Review Always**: Every change gets reviewed, even solo work.
3. **Evidence Over Claims**: Never claim "it works" without running tests.
4. **Guard Everything**: Transition guards enforce quality at each pipeline step.
5. **Immutability**: Create new objects, never mutate existing ones.

## Pipeline Principles

1. **Serial by Default**: Steps execute in order. Guards enforce transitions.
2. **Approval Gates**: Human review required before commits.
3. **Fail Safe**: Pipeline stops on guard failure, never proceeds with bad data.
4. **Audit Trail**: Every decision recorded via structured JSON output.

## Skill Principles

1. **One Skill, One Job**: Each skill handles exactly one concern.
2. **Schema Contracts**: Input/output defined by JSON schema.
3. **Composable**: Skills can be chained in any order the pipeline defines.
4. **Replaceable**: Any skill can be swapped without changing the pipeline.
