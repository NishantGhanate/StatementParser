"""
AST (Abstract Syntax Tree) node classes for Transaction Categorization DSL.

Inspired by lux DSL but simplified for transaction categorization rules.

Example DSL:
    rule "Family Transfer" where entity_name:c:"KANTI" and _raw_type:eq:"debit"
        assign category_id:1 tag_id:2 priority 10;

    rule "Large Transaction" where amount:gt:"50000"
        assign tag_id:3 priority 100;

    rule "UPI Payment" where description:s:"UPI/"
        assign payment_method_id:1 priority 50;
"""

from dataclasses import dataclass, field
from typing import List, Union


# =============================================================================
# FILTER OPERATORS
# =============================================================================

@dataclass
class EqualOperator:
    """Exact equality check"""
    value: str
    case_sensitive: bool = True


@dataclass
class NotEqualOperator:
    """Not equal check"""
    value: str
    case_sensitive: bool = True


@dataclass
class GreaterThanOperator:
    """Greater than comparison (for amounts)"""
    value: str


@dataclass
class LessThanOperator:
    """Less than comparison (for amounts)"""
    value: str


@dataclass
class GreaterThanEqualOperator:
    """Greater than or equal comparison"""
    value: str


@dataclass
class LessThanEqualOperator:
    """Less than or equal comparison"""
    value: str


@dataclass
class BetweenOperator:
    """Between two values (inclusive)"""
    low: str
    high: str


@dataclass
class ContainsOperator:
    """Contains substring check"""
    values: List[str]
    case_sensitive: bool = True


@dataclass
class NotContainsOperator:
    """Does not contain substring check"""
    values: List[str]
    case_sensitive: bool = True


@dataclass
class StartsWithOperator:
    """Starts with check"""
    value: str
    case_sensitive: bool = True


@dataclass
class EndsWithOperator:
    """Ends with check"""
    value: str
    case_sensitive: bool = True


@dataclass
class RegexOperator:
    """Regex pattern match"""
    pattern: str
    case_sensitive: bool = True


@dataclass
class InOperator:
    """Value in list check"""
    values: List[str]
    case_sensitive: bool = True


@dataclass
class NotInOperator:
    """Value not in list check"""
    values: List[str]
    case_sensitive: bool = True


@dataclass
class NullOperator:
    """Is null/empty check"""
    pass


@dataclass
class NotNullOperator:
    """Is not null/empty check"""
    pass


# Type alias for all operators
FilterOperatorType = Union[
    EqualOperator, NotEqualOperator,
    GreaterThanOperator, LessThanOperator,
    GreaterThanEqualOperator, LessThanEqualOperator,
    BetweenOperator,
    ContainsOperator, NotContainsOperator,
    StartsWithOperator, EndsWithOperator,
    RegexOperator,
    InOperator, NotInOperator,
    NullOperator, NotNullOperator
]


# =============================================================================
# EXPRESSION NODES
# =============================================================================

@dataclass
class FilterExpression:
    """Single filter condition: field + operator"""
    field: str
    operator: FilterOperatorType


# =============================================================================
# CONDITION BLOCKS
# =============================================================================

@dataclass
class AndBlock:
    """Multiple conditions combined with AND"""
    conditions: List[FilterExpression]


@dataclass
class OrBlock:
    """Multiple AND blocks combined with OR"""
    blocks: List[AndBlock]


# =============================================================================
# ASSIGNMENT NODE
# =============================================================================

@dataclass
class Assignment:
    """What to assign when rule matches"""
    category_id: int | None = None
    tag_id: int | None = None
    type_id: int | None = None
    payment_method_id: int | None = None
    goal_id:  int | None = None


# =============================================================================
# ROOT NODE - CATEGORIZATION RULE
# =============================================================================

@dataclass
class CategorizationRule:
    """Complete categorization rule"""
    name: str
    conditions: OrBlock  # OR of AND blocks
    assignment: Assignment
    priority: int = 100  # Lower = higher priority
    is_active: bool = True

    def __post_init__(self):
        if not self.conditions.blocks:
            raise ValueError("Rule must have at least one condition block")
