"""
Database storage and retrieval for categorization rules.

Stores rules as DSL text in database, parses on load.
"""
import logging
from typing import List, Optional
from app.rule_engine.ast_nodes import (
    CategorizationRule, OrBlock, AndBlock, FilterExpression, Assignment,
    EqualOperator, NotEqualOperator, GreaterThanOperator, LessThanOperator,
    GreaterThanEqualOperator, LessThanEqualOperator, BetweenOperator,
    ContainsOperator, NotContainsOperator, StartsWithOperator, EndsWithOperator,
    RegexOperator, InOperator, NotInOperator, NullOperator, NotNullOperator
)
from .parser import parse

logger = logging.getLogger("app")

# =============================================================================
# DATABASE SCHEMA
# =============================================================================

SCHEMA_SQL = """
-- Categorization rules table
CREATE TABLE IF NOT EXISTS ss_categorization_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES ss_users(id) ON DELETE CASCADE,
    dsl_text TEXT NOT NULL,  -- Store the DSL rule text
    priority INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_rules_active_priority
    ON ss_categorization_rules (is_active, priority);

-- Function to validate DSL on insert/update
CREATE OR REPLACE FUNCTION validate_categorization_rule()
RETURNS TRIGGER AS $$
BEGIN
    -- Basic validation - just check it's not empty
    IF NEW.dsl_text IS NULL OR LENGTH(TRIM(NEW.dsl_text)) = 0 THEN
        RAISE EXCEPTION 'DSL text cannot be empty';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for validation
DROP TRIGGER IF EXISTS validate_rule_trigger ON ss_categorization_rules;
CREATE TRIGGER validate_rule_trigger
    BEFORE INSERT OR UPDATE ON ss_categorization_rules
    FOR EACH ROW EXECUTE FUNCTION validate_categorization_rule();
"""


# =============================================================================
# SAMPLE DATA
# =============================================================================

SAMPLE_RULES_SQL = """
-- Family transfers (high priority)
INSERT INTO ss_categorization_rules (name, dsl_text, priority) VALUES
('Family - Kanti', 'rule "Family - Kanti" where entity_name:c:"KANTI":i assign category_id:1 tag_id:1 priority 10;', 10);

-- Payment method detection
INSERT INTO ss_categorization_rules (name, dsl_text, priority) VALUES
('UPI Payment', 'rule "UPI Payment" where description:s:"UPI/":i assign payment_method_id:1 priority 50;', 50);

INSERT INTO ss_categorization_rules (name, dsl_text, priority) VALUES
('NEFT Payment', 'rule "NEFT Payment" where description:s:"NEFT":i assign payment_method_id:2 priority 50;', 50);

INSERT INTO ss_categorization_rules (name, dsl_text, priority) VALUES
('IMPS Payment', 'rule "IMPS Payment" where description:s:"IMPS":i assign payment_method_id:3 priority 50;', 50);

-- Transaction type detection
INSERT INTO ss_categorization_rules (name, dsl_text, priority) VALUES
('Type - Credit', 'rule "Type - Credit" where _raw_type:eq:"credit" assign type_id:1 priority 200;', 200);

INSERT INTO ss_categorization_rules (name, dsl_text, priority) VALUES
('Type - Debit', 'rule "Type - Debit" where _raw_type:eq:"debit" assign type_id:2 priority 200;', 200);

-- Large transaction tags
INSERT INTO ss_categorization_rules (name, dsl_text, priority) VALUES
('Large Transaction > 50k', 'rule "Large Transaction" where amount:gt:"50000" assign tag_id:2 priority 100;', 100);

-- Salary detection
INSERT INTO ss_categorization_rules (name, dsl_text, priority) VALUES
('Salary Credit', 'rule "Salary" where description:regex:"SALARY|PAYROLL":i and _raw_type:eq:"credit" assign category_id:2 priority 20;', 20);

-- ATM withdrawal
INSERT INTO ss_categorization_rules (name, dsl_text, priority) VALUES
('ATM Withdrawal', 'rule "ATM Withdrawal" where description:c:"ATM","CASH":i assign category_id:3 payment_method_id:4 priority 30;', 30);
"""


# =============================================================================
# DATABASE LOADER
# =============================================================================

class RuleLoader:
    """Load categorization rules from database."""

    def __init__(self, conn):
        """
        Args:
            conn: Database connection (psycopg2 or similar)
        """
        self.conn = conn

    def load_rules(self) -> List[CategorizationRule]:
        """Load all active rules from database."""
        query = """
            SELECT id, name, dsl_text, priority, is_active
            FROM ss_categorization_rules
            WHERE is_active = TRUE
            ORDER BY priority ASC
        """

        with self.conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

        rules = []
        for row in rows:
            db_id, name, dsl_text, priority, is_active = row
            try:
                rule = parse(dsl_text)
                rule.priority = priority  # Override with DB priority
                rule.is_active = is_active
                rules.append(rule)
            except Exception as e:
                # Log error but continue loading other rules
                logger.exception(f"Error parsing rule {db_id} ({name}): {e}")

        return rules

    def save_rule(self, name: str, dsl_text: str, priority: int = 100) -> int:
        """Save a new rule to database. Returns rule ID."""
        # Validate DSL first
        parse(dsl_text)  # Raises if invalid

        query = """
            INSERT INTO ss_categorization_rules (name, dsl_text, priority)
            VALUES (%s, %s, %s)
            RETURNING id
        """

        with self.conn.cursor() as cur:
            cur.execute(query, (name, dsl_text, priority))
            rule_id = cur.fetchone()[0]
            self.conn.commit()

        return rule_id

    def update_rule(self, rule_id: int, dsl_text: str, priority: Optional[int] = None):
        """Update an existing rule."""
        # Validate DSL first
        logger.debug(dsl_text)  # Raises if invalid

        if priority is not None:
            query = """
                UPDATE ss_categorization_rules
                SET dsl_text = %s, priority = %s, updated_at = NOW()
                WHERE id = %s
            """
            params = (dsl_text, priority, rule_id)
        else:
            query = """
                UPDATE ss_categorization_rules
                SET dsl_text = %s, updated_at = NOW()
                WHERE id = %s
            """
            params = (dsl_text, rule_id)

        with self.conn.cursor() as cur:
            cur.execute(query, params)
            self.conn.commit()

    def delete_rule(self, rule_id: int):
        """Soft delete a rule (set is_active = FALSE)."""
        query = """
            UPDATE ss_categorization_rules
            SET is_active = FALSE, updated_at = NOW()
            WHERE id = %s
        """

        with self.conn.cursor() as cur:
            cur.execute(query, (rule_id,))
            self.conn.commit()


# =============================================================================
# AST TO DSL CONVERTER (for round-trip)
# =============================================================================

def ast_to_dsl(rule: CategorizationRule) -> str:
    """Convert AST back to DSL string."""
    parts = [f'rule "{rule.name}" where']

    # Conditions
    or_parts = []
    for and_block in rule.conditions.blocks:
        and_parts = []
        for expr in and_block.conditions:
            and_parts.append(_expr_to_dsl(expr))
        or_parts.append(" and ".join(and_parts))

    parts.append(" or ".join(or_parts))

    # Assignments
    parts.append("assign")
    assign_parts = []
    if rule.assignment.category_id is not None:
        assign_parts.append(f"category_id:{rule.assignment.category_id}")
    if rule.assignment.tag_id is not None:
        assign_parts.append(f"tag_id:{rule.assignment.tag_id}")
    if rule.assignment.type_id is not None:
        assign_parts.append(f"type_id:{rule.assignment.type_id}")
    if rule.assignment.payment_method_id is not None:
        assign_parts.append(f"payment_method_id:{rule.assignment.payment_method_id}")

    parts.append(" ".join(assign_parts))
    parts.append(f"priority {rule.priority};")

    return " ".join(parts)


def _expr_to_dsl(expr: FilterExpression) -> str:
    """Convert expression to DSL."""
    field = expr.field
    op = expr.operator

    if isinstance(op, EqualOperator):
        case_flag = "" if op.case_sensitive else ":i"
        return f'{field}:eq:"{op.value}"{case_flag}'

    if isinstance(op, NotEqualOperator):
        case_flag = "" if op.case_sensitive else ":i"
        return f'{field}:neq:"{op.value}"{case_flag}'

    if isinstance(op, GreaterThanOperator):
        return f'{field}:gt:"{op.value}"'

    if isinstance(op, LessThanOperator):
        return f'{field}:lt:"{op.value}"'

    if isinstance(op, GreaterThanEqualOperator):
        return f'{field}:gte:"{op.value}"'

    if isinstance(op, LessThanEqualOperator):
        return f'{field}:lte:"{op.value}"'

    if isinstance(op, BetweenOperator):
        return f'{field}:between:"{op.low}":"{op.high}"'

    if isinstance(op, ContainsOperator):
        values = ",".join(f'"{v}"' for v in op.values)
        case_flag = "" if op.case_sensitive else ":i"
        return f'{field}:con:{values}{case_flag}'

    if isinstance(op, NotContainsOperator):
        values = ",".join(f'"{v}"' for v in op.values)
        case_flag = "" if op.case_sensitive else ":i"
        return f'{field}:noc:{values}{case_flag}'

    if isinstance(op, StartsWithOperator):
        case_flag = "" if op.case_sensitive else ":i"
        return f'{field}:sw:"{op.value}"{case_flag}'

    if isinstance(op, EndsWithOperator):
        case_flag = "" if op.case_sensitive else ":i"
        return f'{field}:ew:"{op.value}"{case_flag}'

    if isinstance(op, RegexOperator):
        case_flag = "" if op.case_sensitive else ":i"
        return f'{field}:regex:"{op.pattern}"{case_flag}'

    if isinstance(op, InOperator):
        values = ",".join(f'"{v}"' for v in op.values)
        case_flag = "" if op.case_sensitive else ":i"
        return f'{field}:in:{values}{case_flag}'

    if isinstance(op, NotInOperator):
        values = ",".join(f'"{v}"' for v in op.values)
        case_flag = "" if op.case_sensitive else ":i"
        return f'{field}:nin:{values}{case_flag}'

    if isinstance(op, NullOperator):
        return f'{field}:null'

    if isinstance(op, NotNullOperator):
        return f'{field}:nnull'

    raise ValueError(f"Unknown operator type: {type(op)}")
