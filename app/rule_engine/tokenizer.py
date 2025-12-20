"""
Tokenizer for Transaction Categorization DSL.

Tokens:
    Keywords: rule, where, and, or, assign, priority
    Operators: eq, neq, gt, lt, gte, lte, between, c, nc, s, e, regex, in, nin, null, nnull
    Symbols: :, ;, ,, (, )
    Literals: STRING (quoted), NUMBER, IDENTIFIER
"""

import re
from dataclasses import dataclass
from typing import List
from enum import Enum


class TokenType(Enum):
    # Keywords
    RULE = "RULE"
    WHERE = "WHERE"
    AND = "AND"
    OR = "OR"
    ASSIGN = "ASSIGN"
    PRIORITY = "PRIORITY"

    # Filter operators
    EQ = "EQ"
    NEQ = "NEQ"
    GT = "GT"
    LT = "LT"
    GTE = "GTE"
    LTE = "LTE"
    BETWEEN = "BETWEEN"
    CON = "CON"         # contains
    NOC = "NOC"       # not contains
    SW = "SW"         # starts with
    EW = "EW"         # ends with
    REGEX = "REGEX"
    IN = "IN"
    NIN = "NIN"
    NULL = "NULL"
    NNULL = "NNULL"

    # Assignment fields
    CATEGORY_ID = "CATEGORY_ID"
    TAG_ID = "TAG_ID"
    TYPE_ID = "TYPE_ID"
    PAYMENT_METHOD_ID = "PAYMENT_METHOD_ID"

    # Literals & identifiers
    STRING = "STRING"
    NUMBER = "NUMBER"
    IDENTIFIER = "IDENTIFIER"

    # Symbols
    COLON = "COLON"
    SEMICOLON = "SEMICOLON"
    COMMA = "COMMA"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"

    # End of file
    EOF = "EOF"


@dataclass
class Token:
    type: TokenType
    value: str
    position: int


class TokenError(Exception):
    def __init__(self, message: str, position: int):
        self.position = position
        super().__init__(f"{message} at position {position}")


class Tokenizer:
    # Pattern order matters - longer/more specific patterns first
    PATTERNS = [
        # Keywords (case-insensitive)
        (TokenType.RULE, r'(?i)\brule\b'),
        (TokenType.WHERE, r'(?i)\bwhere\b'),
        (TokenType.AND, r'(?i)\band\b'),
        (TokenType.OR, r'(?i)\bor\b'),
        (TokenType.ASSIGN, r'(?i)\bassign\b'),
        (TokenType.PRIORITY, r'(?i)\bpriority\b'),

        # Filter operators
        (TokenType.EQ, r'(?i)\beq\b'),
        (TokenType.NEQ, r'(?i)\bneq\b'),
        (TokenType.GTE, r'(?i)\bgte\b'),
        (TokenType.LTE, r'(?i)\blte\b'),
        (TokenType.GT, r'(?i)\bgt\b'),
        (TokenType.LT, r'(?i)\blt\b'),
        (TokenType.BETWEEN, r'(?i)\bbetween\b'),
        (TokenType.NOC, r'(?i)\bnoc\b'),
        (TokenType.CON, r'(?i)\bcon\b'),
        (TokenType.SW, r'(?i)\bsw\b'),
        (TokenType.EW, r'(?i)\bew\b'),
        (TokenType.REGEX, r'(?i)\bregex\b'),
        (TokenType.NIN, r'(?i)\bnin\b'),
        (TokenType.IN, r'(?i)\bin\b'),
        (TokenType.NNULL, r'(?i)\bnnull\b'),
        (TokenType.NULL, r'(?i)\bnull\b'),

        # Assignment field names
        (TokenType.CATEGORY_ID, r'(?i)\bcategory_id\b'),
        (TokenType.TAG_ID, r'(?i)\btag_id\b'),
        (TokenType.TYPE_ID, r'(?i)\btype_id\b'),
        (TokenType.PAYMENT_METHOD_ID, r'(?i)\bpayment_method_id\b'),

        # Literals
        (TokenType.STRING, r'"([^"]*)"'),
        (TokenType.NUMBER, r'\d+(?:\.\d+)?'),
        (TokenType.IDENTIFIER, r'[a-zA-Z_][a-zA-Z0-9_]*'),

        # Symbols
        (TokenType.COLON, r':'),
        (TokenType.SEMICOLON, r';'),
        (TokenType.COMMA, r','),
        (TokenType.LPAREN, r'\('),
        (TokenType.RPAREN, r'\)'),
    ]

    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def tokenize(self) -> List[Token]:
        tokens = []

        while self.pos < len(self.text):
            # Skip whitespace
            if self.text[self.pos].isspace():
                self.pos += 1
                continue

            # Skip comments (# to end of line)
            if self.text[self.pos] == '#':
                while self.pos < len(self.text) and self.text[self.pos] != '\n':
                    self.pos += 1
                continue

            matched = False
            for token_type, pattern in self.PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(self.text, self.pos)
                if match:
                    # For STRING, extract the inner value (without quotes)
                    value = match.group(1) if token_type == TokenType.STRING else match.group(0)
                    tokens.append(Token(token_type, value, self.pos))
                    self.pos = match.end()
                    matched = True
                    break

            if not matched:
                raise TokenError(f"Unexpected character '{self.text[self.pos]}'", self.pos)

        tokens.append(Token(TokenType.EOF, "", self.pos))
        return tokens
