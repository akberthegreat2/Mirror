"""Safe step-condition evaluation for Mirror Core.

ADR-0038 extracts the condition evaluator from the executor so the grammar can
be documented and maintained as a small, isolated runtime component.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel

from mirror_core.exceptions import ExecutionError


class ConditionEvaluator:
    """Safely evaluate a restricted boolean expression against runtime inputs."""

    def evaluate(self, condition: str, inputs: Mapping[str, Any]) -> bool:
        normalized = condition.strip().lower()
        if normalized in {"true", "false"}:
            return normalized == "true"
        try:
            tree = ast.parse(condition, mode="eval")
        except SyntaxError as exc:  # pragma: no cover - exercised via executor tests
            raise ExecutionError(
                f"Invalid condition expression: {condition!r}"
            ) from exc
        return bool(self._evaluate(tree, inputs, condition))

    def _evaluate(
        self, node: ast.AST, inputs: Mapping[str, Any], condition: str
    ) -> Any:
        if isinstance(node, ast.Expression):
            return self._evaluate(node.body, inputs, condition)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in inputs:
                raise ExecutionError(f"Unknown condition variable: {node.id!r}")
            return inputs[node.id]
        if isinstance(node, ast.Attribute):
            owner = self._evaluate(node.value, inputs, condition)
            if (
                isinstance(owner, BaseModel)
                and node.attr in owner.__class__.model_fields
            ):
                return getattr(owner, node.attr)
            if isinstance(owner, Mapping) and node.attr in owner:
                return owner[node.attr]
            raise ExecutionError(f"Unknown condition attribute: {node.attr!r}")
        if isinstance(node, ast.BoolOp):
            values = [
                bool(self._evaluate(value, inputs, condition)) for value in node.values
            ]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not bool(self._evaluate(node.operand, inputs, condition))
        if isinstance(node, ast.Compare):
            left = self._evaluate(node.left, inputs, condition)
            for op, comparator in zip(node.ops, node.comparators, strict=True):
                right = self._evaluate(comparator, inputs, condition)
                ok = (
                    left == right
                    if isinstance(op, ast.Eq)
                    else left != right
                    if isinstance(op, ast.NotEq)
                    else left < right
                    if isinstance(op, ast.Lt)
                    else left <= right
                    if isinstance(op, ast.LtE)
                    else left > right
                    if isinstance(op, ast.Gt)
                    else left >= right
                    if isinstance(op, ast.GtE)
                    else None
                )
                if ok is None:
                    raise ExecutionError(f"Unsupported comparison in {condition!r}")
                if not ok:
                    return False
                left = right
            return True
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "exists"
        ):
            if len(node.args) != 1 or node.keywords:
                raise ExecutionError(f"exists() expects one argument in {condition!r}")
            arg = node.args[0]
            if isinstance(arg, ast.Name):
                return arg.id in inputs
            try:
                return self._evaluate(arg, inputs, condition) is not None
            except ExecutionError:
                return False
        raise ExecutionError(f"Unsupported condition expression: {condition!r}")


__all__ = ["ConditionEvaluator"]
