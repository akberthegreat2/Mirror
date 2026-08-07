# Condition grammar

Mirror uses a deliberately small boolean expression grammar for step conditions.

## Supported forms

- boolean literals: `true`, `false`
- names resolved from the runtime input mapping
- dotted attribute access on values already resolved from inputs
- boolean operators: `and`, `or`, `not`
- comparisons: `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not in`
- the helper function `exists(value)`

## Example

```python
customer_id and exists(customer_id) and status == "ready"
```

## Safety rules

The evaluator rejects anything outside the allowlist above.
It does not execute arbitrary Python code.
It raises `ExecutionError` when the expression is invalid, references an unknown input, or uses an unsupported AST node.

## Extension rule

Any future addition to the grammar must be documented here and covered by tests before it is used by new runtime policies.
