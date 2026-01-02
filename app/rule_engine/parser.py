"""
Parser for Transaction Categorization DSL.

Syntax:
    rule "Rule Name" where <conditions> assign <assignments> priority <number>;

Conditions:
    field:operator:value [and|or field:operator:value ...]

Operators:
    eq, neq      - equality (with optional :i for case-insensitive)
    gt, lt       - comparison
    gte, lte     - comparison with equals
    between      - range (field:between:"low":"high")
    c, nc        - contains, not contains
    s, e         - starts with, ends with
    regex        - regex pattern
    in, nin      - in list, not in list
    null, nnull  - null checks

Assignments:
    category_id:N tag_id:N type_id:N payment_method_id:N

Examples:
    rule "Family Transfer" where entity_name:c:"KANTI" assign category_id:1 priority 10;
    rule "UPI Payment" where description:s:"UPI/":i and _raw_type:eq:"debit" assign payment_method_id:1 type_id:2 priority 50;
    rule "Large Debit" where amount:gt:"50000" and _raw_type:eq:"debit" assign tag_id:3 priority 100;
"""

from typing import List, Optional

from .tokenizer import Tokenizer, Token, TokenType, TokenError
from .ast_nodes import (
    CategorizationRule, OrBlock, AndBlock, FilterExpression, Assignment,
    EqualOperator, NotEqualOperator, GreaterThanOperator, LessThanOperator,
    GreaterThanEqualOperator, LessThanEqualOperator, BetweenOperator,
    ContainsOperator, NotContainsOperator, StartsWithOperator, EndsWithOperator,
    RegexOperator, InOperator, NotInOperator, NullOperator, NotNullOperator
)


class ParseError(Exception):
    def __init__(self, message: str, position: int):
        self.position = position
        super().__init__(f"{message} at position {position}")


class Parser:
    def __init__(self, text: str):
        self.tokens = Tokenizer(text).tokenize()
        self.pos = 0

    def parse(self) -> CategorizationRule:
        """Parse a single rule."""
        rule = self._parse_rule()
        self._expect(TokenType.EOF)
        return rule

    def parse_multiple(self) -> List[CategorizationRule]:
        """Parse multiple rules from text."""
        rules = []
        while not self._peek(TokenType.EOF):
            rules.append(self._parse_rule())
        return rules

    def _parse_rule(self) -> CategorizationRule:
        """Parse: rule "name" where <conditions> assign <assignments> priority <number>;"""
        self._expect(TokenType.RULE)

        # Rule name
        name = self._expect(TokenType.STRING).value

        # Conditions
        self._expect(TokenType.WHERE)
        conditions = self._parse_conditions()

        # Assignments
        self._expect(TokenType.ASSIGN)
        assignment = self._parse_assignments()

        # Priority (optional)
        priority = 100
        if self._peek(TokenType.PRIORITY):
            self._advance()
            priority = int(self._expect(TokenType.NUMBER).value)

        self._expect(TokenType.SEMICOLON)

        return CategorizationRule(
            name=name,
            conditions=conditions,
            assignment=assignment,
            priority=priority
        )

    def _parse_conditions(self) -> OrBlock:
        """Parse OR-separated AND blocks."""
        blocks = [self._parse_and_block()]

        while self._peek(TokenType.OR):
            self._advance()
            blocks.append(self._parse_and_block())

        return OrBlock(blocks)

    def _parse_and_block(self) -> AndBlock:
        """Parse AND-separated filter expressions."""
        conditions = [self._parse_filter_expr()]

        while self._peek(TokenType.AND):
            self._advance()
            conditions.append(self._parse_filter_expr())

        return AndBlock(conditions)

    def _parse_filter_expr(self) -> FilterExpression:
        """Parse: field:operator[:value][:i]"""
        field = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.COLON)
        operator = self._parse_operator()

        return FilterExpression(field, operator)

    def _parse_operator(self):
        """Parse filter operator with value."""
        current = self._current()

        # EQ operator
        if current.type == TokenType.EQ:
            self._advance()
            self._expect(TokenType.COLON)
            value = self._expect(TokenType.STRING).value
            case_sensitive = self._parse_case_flag()
            return EqualOperator(value, case_sensitive)

        # NEQ operator
        elif current.type == TokenType.NEQ:
            self._advance()
            self._expect(TokenType.COLON)
            value = self._expect(TokenType.STRING).value
            case_sensitive = self._parse_case_flag()
            return NotEqualOperator(value, case_sensitive)

        # GT operator
        elif current.type == TokenType.GT:
            self._advance()
            self._expect(TokenType.COLON)
            value = self._expect(TokenType.STRING).value
            return GreaterThanOperator(value)

        # LT operator
        elif current.type == TokenType.LT:
            self._advance()
            self._expect(TokenType.COLON)
            value = self._expect(TokenType.STRING).value
            return LessThanOperator(value)

        # GTE operator
        elif current.type == TokenType.GTE:
            self._advance()
            self._expect(TokenType.COLON)
            value = self._expect(TokenType.STRING).value
            return GreaterThanEqualOperator(value)

        # LTE operator
        elif current.type == TokenType.LTE:
            self._advance()
            self._expect(TokenType.COLON)
            value = self._expect(TokenType.STRING).value
            return LessThanEqualOperator(value)

        # BETWEEN operator
        elif current.type == TokenType.BETWEEN:
            self._advance()
            self._expect(TokenType.COLON)
            low = self._expect(TokenType.STRING).value
            self._expect(TokenType.COLON)
            high = self._expect(TokenType.STRING).value
            return BetweenOperator(low, high)

        # Contains operator
        elif current.type == TokenType.CON:
            self._advance()
            self._expect(TokenType.COLON)
            values = self._parse_string_list()
            case_sensitive = self._parse_case_flag()
            return ContainsOperator(values, case_sensitive)

        # Not contains operator
        elif current.type == TokenType.NOC:
            self._advance()
            self._expect(TokenType.COLON)
            values = self._parse_string_list()
            case_sensitive = self._parse_case_flag()
            return NotContainsOperator(values, case_sensitive)

        # Starts with operator
        elif current.type == TokenType.SW:
            self._advance()
            self._expect(TokenType.COLON)
            value = self._expect(TokenType.STRING).value
            case_sensitive = self._parse_case_flag()
            return StartsWithOperator(value, case_sensitive)

        # Ends with operator
        elif current.type == TokenType.EW:
            self._advance()
            self._expect(TokenType.COLON)
            value = self._expect(TokenType.STRING).value
            case_sensitive = self._parse_case_flag()
            return EndsWithOperator(value, case_sensitive)

        # Regex operator
        elif current.type == TokenType.REGEX:
            self._advance()
            self._expect(TokenType.COLON)
            pattern = self._expect(TokenType.STRING).value
            case_sensitive = self._parse_case_flag()
            return RegexOperator(pattern, case_sensitive)

        # IN operator
        elif current.type == TokenType.IN:
            self._advance()
            self._expect(TokenType.COLON)
            values = self._parse_string_list()
            case_sensitive = self._parse_case_flag()
            return InOperator(values, case_sensitive)

        # NIN operator
        elif current.type == TokenType.NIN:
            self._advance()
            self._expect(TokenType.COLON)
            values = self._parse_string_list()
            case_sensitive = self._parse_case_flag()
            return NotInOperator(values, case_sensitive)

        # NULL operator
        elif current.type == TokenType.NULL:
            self._advance()
            return NullOperator()

        # NNULL operator
        elif current.type == TokenType.NNULL:
            self._advance()
            return NotNullOperator()

        else:
            raise ParseError(f"Unknown operator {current.type} - '{current.value}'", current.position)

    def _parse_case_flag(self) -> bool:
        """Parse optional :i flag for case-insensitive."""
        if self._peek(TokenType.COLON):
            # Check if next token after colon is 'i' identifier
            next_pos = self.pos + 1
            if next_pos < len(self.tokens):
                next_token = self.tokens[next_pos]
                if next_token.type == TokenType.IDENTIFIER and next_token.value.lower() == 'i':
                    self._advance()  # consume :
                    self._advance()  # consume i
                    return False
        return True

    def _parse_string_list(self) -> List[str]:
        """Parse comma-separated quoted strings."""
        values = [self._expect(TokenType.STRING).value]

        while self._peek(TokenType.COMMA):
            self._advance()
            values.append(self._expect(TokenType.STRING).value)

        return values

    def _parse_assignments(self) -> Assignment:
        """Parse: category_id:N tag_id:N type_id:N payment_method_id:N goal_id:N"""
        assignment = Assignment()

        while self._current().type in (
            TokenType.CATEGORY_ID, TokenType.TAG_ID,
            TokenType.TYPE_ID, TokenType.PAYMENT_METHOD_ID, TokenType.GOAL_ID
        ):
            field_type = self._advance().type
            self._expect(TokenType.COLON)
            value = int(self._expect(TokenType.NUMBER).value)

            if field_type == TokenType.CATEGORY_ID:
                assignment.category_id = value
            elif field_type == TokenType.TAG_ID:
                assignment.tag_id = value
            elif field_type == TokenType.TYPE_ID:
                assignment.type_id = value
            elif field_type == TokenType.PAYMENT_METHOD_ID:
                assignment.payment_method_id = value
            elif field_type == TokenType.GOAL_ID:
                assignment.goal_id = value

        return assignment

    # Helper methods
    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self, token_type: TokenType) -> bool:
        return self._current().type == token_type

    def _advance(self) -> Token:
        token = self._current()
        if token.type != TokenType.EOF:
            self.pos += 1
        return token

    def _expect(self, token_type: TokenType) -> Token:
        if not self._peek(token_type):
            current = self._current()
            raise ParseError(f"Expected {token_type.value}, got {current.type.value}", current.position)
        return self._advance()


# =============================================================================
# PUBLIC API
# =============================================================================

def parse(code: str) -> CategorizationRule:
    """Parse single categorization rule from DSL code."""
    return Parser(code).parse()


def parse_rules(code: str) -> List[CategorizationRule]:
    """Parse multiple categorization rules from DSL code."""
    return Parser(code).parse_multiple()


def try_parse(code: str) -> tuple[Optional[CategorizationRule], Optional[str]]:
    """Try to parse, returning (result, error)."""
    try:
        return parse(code), None
    except (ParseError, TokenError) as e:
        return None, str(e)
