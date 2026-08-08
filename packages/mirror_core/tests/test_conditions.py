"""Direct regression tests for the restricted condition evaluator."""

from __future__ import annotations

import pytest
from mirror_core.conditions import ConditionEvaluator
from mirror_core.exceptions import ExecutionError
from pydantic import BaseModel


class User(BaseModel):
    active: bool
    profile: dict[str, object]


def test_literals_and_names() -> None:
    evaluator = ConditionEvaluator()
    assert evaluator.evaluate("true", {}) is True
    assert evaluator.evaluate("FALSE", {}) is False
    assert evaluator.evaluate("enabled", {"enabled": True}) is True


def test_nested_attributes_support_models_and_mappings() -> None:
    evaluator = ConditionEvaluator()
    user = User(active=True, profile={"tier": "pro"})
    assert evaluator.evaluate("user.active", {"user": user}) is True
    assert evaluator.evaluate("user.profile.tier == 'pro'", {"user": user}) is True


def test_boolean_operators_and_unary_not() -> None:
    evaluator = ConditionEvaluator()
    inputs = {"a": True, "b": False, "c": True}
    assert evaluator.evaluate("a and c", inputs) is True
    assert evaluator.evaluate("a and b or c", inputs) is True
    assert evaluator.evaluate("not b", inputs) is True


def test_chained_comparisons() -> None:
    evaluator = ConditionEvaluator()
    assert evaluator.evaluate("1 < value <= 3", {"value": 2}) is True
    assert evaluator.evaluate("1 < value <= 3", {"value": 4}) is False


def test_exists_handles_names_and_values() -> None:
    evaluator = ConditionEvaluator()
    assert evaluator.evaluate("exists(value)", {"value": 1}) is True
    assert evaluator.evaluate("exists(value)", {"value": None}) is True
    assert evaluator.evaluate("exists(missing)", {}) is False


def test_unknown_variables_and_attributes_are_rejected() -> None:
    evaluator = ConditionEvaluator()
    with pytest.raises(ExecutionError):
        evaluator.evaluate("missing", {})
    with pytest.raises(ExecutionError):
        evaluator.evaluate("user.secret", {"user": User(active=True, profile={})})


@pytest.mark.parametrize(
    "condition",
    [
        "__import__('os').system('echo unsafe')",
        "user.__class__",
        "user.__class__.__bases__",
        "(lambda: True)()",
        "[x for x in range(3)]",
        "{x: x for x in range(3)}",
        "open('/tmp/mirror-condition-test', 'w')",
    ],
)
def test_unsafe_python_constructs_are_rejected(condition: str) -> None:
    evaluator = ConditionEvaluator()
    with pytest.raises(ExecutionError):
        evaluator.evaluate(condition, {"user": User(active=True, profile={})})


def test_unsupported_call_and_operator_are_rejected() -> None:
    evaluator = ConditionEvaluator()
    with pytest.raises(ExecutionError):
        evaluator.evaluate("str(value)", {"value": 1})
    with pytest.raises(ExecutionError):
        evaluator.evaluate("value in values", {"value": 1, "values": [1, 2]})


def test_malformed_expression_is_rejected() -> None:
    evaluator = ConditionEvaluator()
    with pytest.raises(ExecutionError, match="Invalid condition expression"):
        evaluator.evaluate("value and", {"value": True})
