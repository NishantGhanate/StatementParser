"""
Evaluator for Transaction Categorization Rules.

Takes parsed AST and evaluates against transaction dictionaries.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List

from .ast_nodes import (
    CategorizationRule, OrBlock, AndBlock, FilterExpression,
    EqualOperator, NotEqualOperator, GreaterThanOperator, LessThanOperator,
    GreaterThanEqualOperator, LessThanEqualOperator, BetweenOperator,
    ContainsOperator, NotContainsOperator, StartsWithOperator, EndsWithOperator,
    RegexOperator, InOperator, NotInOperator, NullOperator, NotNullOperator
)


class RuleEvaluator:
    """Evaluates categorization rules against transactions."""

    def evaluate_rule(self, rule: CategorizationRule, transaction: Dict[str, Any]) -> bool:
        """Check if a rule matches a transaction."""
        if not rule.is_active:
            return False
        return self._evaluate_or_block(rule.conditions, transaction)

    def _evaluate_or_block(self, or_block: OrBlock, transaction: Dict[str, Any]) -> bool:
        """Evaluate OR block - any AND block must match."""
        return any(
            self._evaluate_and_block(and_block, transaction)
            for and_block in or_block.blocks
        )

    def _evaluate_and_block(self, and_block: AndBlock, transaction: Dict[str, Any]) -> bool:
        """Evaluate AND block - all conditions must match."""
        return all(
            self._evaluate_expression(expr, transaction)
            for expr in and_block.conditions
        )

    def _evaluate_expression(self, expr: FilterExpression, transaction: Dict[str, Any]) -> bool:
        """Evaluate single filter expression."""
        field_value = transaction.get(expr.field)
        operator = expr.operator

        # Handle null checks first
        if isinstance(operator, NullOperator):
            return field_value is None or field_value == ""

        if isinstance(operator, NotNullOperator):
            return field_value is not None and field_value != ""

        # For other operators, null field means no match
        if field_value is None:
            return False

        # Convert field value to string for string operations
        field_str = str(field_value)

        # Equality operators
        if isinstance(operator, EqualOperator):
            return self._str_equals(field_str, operator.value, operator.case_sensitive)

        if isinstance(operator, NotEqualOperator):
            return not self._str_equals(field_str, operator.value, operator.case_sensitive)

        # Comparison operators (for numeric/string comparison)
        if isinstance(operator, GreaterThanOperator):
            return self._compare_values(field_value, operator.value) > 0

        if isinstance(operator, LessThanOperator):
            return self._compare_values(field_value, operator.value) < 0

        if isinstance(operator, GreaterThanEqualOperator):
            return self._compare_values(field_value, operator.value) >= 0

        if isinstance(operator, LessThanEqualOperator):
            return self._compare_values(field_value, operator.value) <= 0

        if isinstance(operator, BetweenOperator):
            cmp_low = self._compare_values(field_value, operator.low)
            cmp_high = self._compare_values(field_value, operator.high)
            return cmp_low >= 0 and cmp_high <= 0

        # Contains operators
        if isinstance(operator, ContainsOperator):
            return self._str_contains_any(field_str, operator.values, operator.case_sensitive)

        if isinstance(operator, NotContainsOperator):
            return not self._str_contains_any(field_str, operator.values, operator.case_sensitive)

        # Starts/ends with
        if isinstance(operator, StartsWithOperator):
            return self._str_starts_with(field_str, operator.value, operator.case_sensitive)

        if isinstance(operator, EndsWithOperator):
            return self._str_ends_with(field_str, operator.value, operator.case_sensitive)

        # Regex
        if isinstance(operator, RegexOperator):
            flags = 0 if operator.case_sensitive else re.IGNORECASE
            return bool(re.search(operator.pattern, field_str, flags))

        # In/not in
        if isinstance(operator, InOperator):
            return self._str_in_list(field_str, operator.values, operator.case_sensitive)

        if isinstance(operator, NotInOperator):
            return not self._str_in_list(field_str, operator.values, operator.case_sensitive)

        return False

    # String helper methods
    def _str_equals(self, a: str, b: str, case_sensitive: bool) -> bool:
        if case_sensitive:
            return a == b
        return a.lower() == b.lower()

    def _str_contains_any(self, haystack: str, needles: List[str], case_sensitive: bool) -> bool:
        if not case_sensitive:
            haystack = haystack.lower()
            needles = [n.lower() for n in needles]
        return any(needle in haystack for needle in needles)

    def _str_starts_with(self, s: str, prefix: str, case_sensitive: bool) -> bool:
        if case_sensitive:
            return s.startswith(prefix)
        return s.lower().startswith(prefix.lower())

    def _str_ends_with(self, s: str, suffix: str, case_sensitive: bool) -> bool:
        if case_sensitive:
            return s.endswith(suffix)
        return s.lower().endswith(suffix.lower())

    def _str_in_list(self, value: str, values: List[str], case_sensitive: bool) -> bool:
        if case_sensitive:
            return value in values
        return value.lower() in [v.lower() for v in values]

    def _compare_values(self, a: Any, b: str) -> int:
        """Compare values, trying numeric first, then string."""
        try:
            # Try numeric comparison
            num_a = Decimal(str(a))
            num_b = Decimal(b)
            if num_a > num_b:
                return 1
            elif num_a < num_b:
                return -1
            return 0
        except (InvalidOperation, ValueError):
            # Fall back to string comparison
            str_a = str(a)
            if str_a > b:
                return 1
            elif str_a < b:
                return -1
            return 0


class TransactionCategorizer:
    """Applies multiple rules to categorize transactions."""

    def __init__(self, rules: List[CategorizationRule]):
        # Sort by priority (lower = higher priority)
        self.rules = sorted(rules, key=lambda r: r.priority)
        self.evaluator = RuleEvaluator()

    def categorize(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply rules to transaction and return enriched transaction.
        First matching rule for each field wins.
        """
        result = transaction.copy()

        # Track which fields have been set
        fields_set = {
            'category_id': result.get('category_id') is not None,
            'tag_id': result.get('tag_id') is not None,
            'type_id': result.get('type_id') is not None,
            'payment_method_id': result.get('payment_method_id') is not None,
        }

        for rule in self.rules:
            # Skip if all fields already set
            if all(fields_set.values()):
                break

            if self.evaluator.evaluate_rule(rule, transaction):
                # Apply assignments for fields not yet set
                assignment = rule.assignment

                if assignment.category_id is not None and not fields_set['category_id']:
                    result['category_id'] = assignment.category_id
                    fields_set['category_id'] = True

                if assignment.tag_id is not None and not fields_set['tag_id']:
                    result['tag_id'] = assignment.tag_id
                    fields_set['tag_id'] = True

                if assignment.type_id is not None and not fields_set['type_id']:
                    result['type_id'] = assignment.type_id
                    fields_set['type_id'] = True

                if assignment.payment_method_id is not None and not fields_set['payment_method_id']:
                    result['payment_method_id'] = assignment.payment_method_id
                    fields_set['payment_method_id'] = True

        return result

    def categorize_batch(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Categorize multiple transactions."""
        return [self.categorize(t) for t in transactions]

    def find_matching_rules(self, transaction: Dict[str, Any]) -> List[CategorizationRule]:
        """Find all rules that match a transaction (for debugging)."""
        return [
            rule for rule in self.rules
            if self.evaluator.evaluate_rule(rule, transaction)
        ]
