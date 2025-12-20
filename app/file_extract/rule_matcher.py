import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

import psycopg2
from psycopg2.extras import RealDictCursor


class MatchField(Enum):
    ENTITY_NAME = "entity_name"
    DESCRIPTION = "description"
    REMARKS = "remarks"
    AMOUNT = "amount"
    TYPE = "type"


class MatchOperator(Enum):
    CONTAINS = "contains"
    EQUALS = "equals"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    BETWEEN = "between"


@dataclass
class Rule:
    id: int
    name: str
    field: MatchField
    operator: MatchOperator
    value: str
    value_secondary: str | None  # For BETWEEN operator
    category_id: int | None
    tag_id: int | None
    type_id: int | None
    payment_method_id: int | None
    priority: int  # Lower = higher priority


class TransactionCategorizer:
    def __init__(self, db_conn):
        self.conn = db_conn
        self.rules: list[Rule] = []
        self.load_rules()

    def load_rules(self):
        """Fetch categorization rules from database"""
        query = """
            SELECT id, name, field, operator, value, value_secondary,
                   category_id, tag_id, type_id, payment_method_id, priority
            FROM ss_categorization_rules
            WHERE is_active = TRUE
            ORDER BY priority ASC
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()

        self.rules = [
            Rule(
                id=row['id'],
                name=row['name'],
                field=MatchField(row['field']),
                operator=MatchOperator(row['operator']),
                value=row['value'],
                value_secondary=row.get('value_secondary'),
                category_id=row['category_id'],
                tag_id=row['tag_id'],
                type_id=row['type_id'],
                payment_method_id=row['payment_method_id'],
                priority=row['priority']
            )
            for row in rows
        ]

    def match_rule(self, rule: Rule, transaction: dict) -> bool:
        """Check if a rule matches the transaction"""
        field_value = transaction.get(rule.field.value)

        if field_value is None:
            return False

        # String operations
        if rule.operator == MatchOperator.CONTAINS:
            return rule.value.lower() in str(field_value).lower()

        elif rule.operator == MatchOperator.EQUALS:
            return str(field_value).lower() == rule.value.lower()

        elif rule.operator == MatchOperator.STARTS_WITH:
            return str(field_value).lower().startswith(rule.value.lower())

        elif rule.operator == MatchOperator.ENDS_WITH:
            return str(field_value).lower().endswith(rule.value.lower())

        elif rule.operator == MatchOperator.REGEX:
            return bool(re.search(rule.value, str(field_value), re.IGNORECASE))

        # Numeric operations (for amount)
        elif rule.operator in (MatchOperator.GREATER_THAN, MatchOperator.LESS_THAN, MatchOperator.BETWEEN):
            try:
                amount = Decimal(str(field_value))
                threshold = Decimal(rule.value)

                if rule.operator == MatchOperator.GREATER_THAN:
                    return amount > threshold
                elif rule.operator == MatchOperator.LESS_THAN:
                    return amount < threshold
                elif rule.operator == MatchOperator.BETWEEN:
                    threshold_high = Decimal(rule.value_secondary)
                    return threshold <= amount <= threshold_high
            except:
                return False

        return False

    def categorize(self, transaction: dict) -> dict:
        """Apply rules to transaction and return enriched transaction"""
        result = transaction.copy()

        for rule in self.rules:
            if self.match_rule(rule, transaction):
                # Only set if not already set (first match wins per field)
                if rule.category_id and not result.get('category_id'):
                    result['category_id'] = rule.category_id

                if rule.tag_id and not result.get('tag_id'):
                    result['tag_id'] = rule.tag_id

                if rule.type_id and not result.get('type_id'):
                    result['type_id'] = rule.type_id

                if rule.payment_method_id and not result.get('payment_method_id'):
                    result['payment_method_id'] = rule.payment_method_id

                # If all fields are set, no need to continue
                if all([
                    result.get('category_id'),
                    result.get('tag_id'),
                    result.get('type_id'),
                    result.get('payment_method_id')
                ]):
                    break

        return result

    def categorize_batch(self, transactions: list[dict]) -> list[dict]:
        """Categorize multiple transactions"""
        return [self.categorize(t) for t in transactions]


# Database schema for rules
RULES_TABLE_SQL = """
CREATE TABLE ss_categorization_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    field VARCHAR(50) NOT NULL,  -- entity_name, description, remarks, amount, _raw_type
    operator VARCHAR(20) NOT NULL,  -- contains, equals, starts_with, ends_with, regex, gt, lt, between
    value TEXT NOT NULL,
    value_secondary TEXT,  -- For 'between' operator
    category_id INTEGER REFERENCES ss_categories(id),
    tag_id INTEGER REFERENCES ss_tags(id),
    type_id INTEGER REFERENCES ss_transaction_types(id),
    payment_method_id INTEGER REFERENCES ss_payment_methods(id),
    priority INTEGER DEFAULT 100,  -- Lower = higher priority
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for faster rule lookups
CREATE INDEX idx_rules_active_priority ON ss_categorization_rules (is_active, priority);
"""

# Sample rules insert
SAMPLE_RULES_SQL = """
-- Family transfers
INSERT INTO ss_categorization_rules (name, field, operator, value, category_id, tag_id, priority)
VALUES ('Family - Kanti', 'entity_name', 'contains', 'KANTI', 1, 1, 10);

-- UPI payments
INSERT INTO ss_categorization_rules (name, field, operator, value, payment_method_id, priority)
VALUES ('Payment Method - UPI', 'description', 'starts_with', 'UPI/', 1, 50);

-- Large transactions
INSERT INTO ss_categorization_rules (name, field, operator, value, tag_id, priority)
VALUES ('Large Transaction', 'amount', 'gt', '50000', 2, 100);

-- Salary credits
INSERT INTO ss_categorization_rules (name, field, operator, value, category_id, priority)
VALUES ('Salary', 'description', 'regex', 'SALARY|PAYROLL', 3, 20);

-- Credit type
INSERT INTO ss_categorization_rules (name, field, operator, value, type_id, priority)
VALUES ('Type - Credit', '_raw_type', 'equals', 'credit', 1, 200);

-- Debit type
INSERT INTO ss_categorization_rules (name, field, operator, value, type_id, priority)
VALUES ('Type - Debit', '_raw_type', 'equals', 'debit', 2, 200);
"""


if __name__ == "__main__":
    # Example usage
    conn = psycopg2.connect("postgresql://user:pass@localhost/dbname")

    categorizer = TransactionCategorizer(conn)

    transaction = {
        "entity_name": "KANTI RAMULU GA",
        "transaction_date": "2025-11-13",
        "person_id": 1,
        "type_id": None,
        "category_id": None,
        "tag_id": None,
        "amount": Decimal("75000.00"),
        "currency": "INR",
        "payment_method_id": None,
        "goal_id": None,
        "description": "UPI/KANTI RAMULU GA/531715436912/PaidViaKotakApp",
        "remarks": "UPI-531746164437",
        "_raw_type": "debit"
    }

    result = categorizer.categorize(transaction)

    print("Categorized transaction:")
    for k, v in result.items():
        print(f"  {k}: {v}")

    conn.close()
