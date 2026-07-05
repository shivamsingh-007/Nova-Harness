# Example Hook: Production Safety Guard

Attaches to `pre_tool_call` to block unsafe operations against production environments.

## Hook Point

- `pre_tool_call`: fires before every tool invocation

## Effect

- `block`: prevents execution when the tool matches a production-safety policy violation

## Failure Policy

- `fail_closed`: if the hook itself fails, the tool call is also blocked (safe side)

## Context Received

- tool name and arguments
- current run/step/loop ids
- policy refs

## Behavior

1. Reads the tool name and arguments from context.
2. Checks against production safety rules.
3. If violation detected: returns BLOCKED with block_reason.
4. Otherwise: returns PASS_THROUGH.
