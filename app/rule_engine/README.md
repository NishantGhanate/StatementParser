# Transaction Categorizer Rule Engine

AST-based rule engine for categorizing financial transactions, inspired by the lux DSL system.

## Features

- **DSL-based rules**: Define categorization rules using a simple, readable syntax
- **Multiple operators**: eq, neq, gt, lt, gte, lte, between, con, noc, starts_with, ends_with, regex, in, nin, null, nnull
- **Case sensitivity control**: Add `:i` flag for case-insensitive matching
- **Priority-based evaluation**: Lower priority number = higher precedence
- **AND/OR logic**: Combine conditions with `and`/`or`
- **Multiple assignments**: Set category_id, tag_id, type_id, payment_method_id in one rule
- **Database integration**: Store rules in PostgreSQL, load and parse on demand

## DSL Syntax

```
rule "Rule Name" where <conditions> assign <assignments> priority <number>;
```

### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equals | `status:eq:"active"` |
| `neq` | Not equals | `status:neq:"inactive"` |
| `gt` | Greater than | `amount:gt:"1000"` |
| `lt` | Less than | `amount:lt:"1000"` |
| `gte` | Greater or equal | `amount:gte:"1000"` |
| `lte` | Less or equal | `amount:lte:"1000"` |
| `between` | Range (inclusive) | `amount:between:"100":"500"` |
| `con` | Contains | `desc:con:"UPI","NEFT"` |
| `noc` | Not contains | `desc:noc:"SPAM"` |
| `starts_with` | Starts with | `desc:starts_with:"UPI/"` |
| `ends_with` | Ends with | `email:ends_with:"@gmail.com"` |
| `regex` | Regex match | `desc:regex:"SALARY\|PAYROLL"` |
| `in` | In list | `status:in:"active","qualified"` |
| `nin` | Not in list | `status:nin:"inactive","dead"` |
| `null` | Is null/empty | `remarks:null` |
| `nnull` | Is not null/empty | `remarks:nnull` |

### Case Insensitivity

Add `:i` at the end of string operators for case-insensitive matching:

```
entity_name:c:"State":i
description:s:"upi/":i
status:eq:"ACTIVE":i
```

### AND/OR Logic

```
# AND: All conditions must match
rule "Test" where field1:eq:"a" and field2:eq:"b" assign category_id:1 priority 10;

# OR: Any condition block must match
rule "Test" where field1:eq:"a" or field2:eq:"b" assign category_id:1 priority 10;

# Complex: (field1 AND field2) OR field3
rule "Test" where field1:eq:"a" and field2:eq:"b" or field3:eq:"c" assign category_id:1 priority 10;
```

## Usage

### Basic Usage

```python
from transaction_categorizer import parse_rules, TransactionCategorizer
from decimal import Decimal

# Define rules
rules_dsl = '''
rule "Family Transfer" where entity_name:c:"KANTI":i assign category_id:1 priority 10;
rule "UPI Payment" where description:s:"UPI/":i assign payment_method_id:1 priority 50;
rule "Large Transaction" where amount:gt:"50000" assign tag_id:2 priority 100;
rule "Debit Type" where _raw_type:eq:"debit" assign type_id:2 priority 200;
'''

# Parse and create categorizer
rules = parse_rules(rules_dsl)
categorizer = TransactionCategorizer(rules)

# Categorize a transaction
transaction = {
    "entity_name": "KANTI RAMULU GA",
    "description": "UPI/KANTI RAMULU GA/123/Payment",
    "_raw_type": "debit",
    "amount": Decimal("75000.00"),
    "category_id": None,
    "tag_id": None,
    "type_id": None,
    "payment_method_id": None,
}

result = categorizer.categorize(transaction)
print(result["category_id"])       # 1 (Family)
print(result["payment_method_id"]) # 1 (UPI)
print(result["tag_id"])            # 2 (Large)
print(result["type_id"])           # 2 (Debit)
```

### Database Integration

```python
import psycopg2
from transaction_categorizer import RuleLoader, TransactionCategorizer, SCHEMA_SQL

# Setup database
conn = psycopg2.connect("postgresql://user:pass@localhost/dbname")
with conn.cursor() as cur:
    cur.execute(SCHEMA_SQL)
conn.commit()

# Load rules from database
loader = RuleLoader(conn)
rules = loader.load_rules()
categorizer = TransactionCategorizer(rules)

# Save a new rule
loader.save_rule(
    name="Family Transfer",
    dsl_text='rule "Family Transfer" where entity_name:c:"KANTI":i assign category_id:1 priority 10;',
    priority=10
)
```

### Debugging

```python
# Find which rules match a transaction
matching_rules = categorizer.find_matching_rules(transaction)
for rule in matching_rules:
    print(f"- {rule.name} (priority: {rule.priority})")
```

## Running Tests

```bash
cd D:\ActivePrime\Repo\lux
pytest poc/transaction_categorizer/test_categorizer.py -v
```

## Running Examples

```bash
cd D:\ActivePrime\Repo\lux
python -m poc.transaction_categorizer.example
```

## Database Schema

```sql
CREATE TABLE ss_categorization_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dsl_text TEXT NOT NULL,
    priority INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Architecture

```
transaction_categorizer/
├── __init__.py          # Public API
├── ast_nodes.py         # AST node definitions
├── tokenizer.py         # Lexical analysis
├── parser.py            # DSL parser
├── evaluator.py         # Rule evaluation engine
├── db.py                # Database integration
├── example.py           # Usage examples
└── test_categorizer.py  # Tests
```

## Key Concepts (from lux DSL)

1. **Tokenizer**: Breaks DSL text into tokens (keywords, operators, values)
2. **Parser**: Converts tokens into AST (Abstract Syntax Tree)
3. **AST Nodes**: Data classes representing rule structure
4. **Evaluator**: Traverses AST and evaluates against data
5. **Categorizer**: Orchestrates multiple rules with priority handling

## DSL (Domain Specific Language)

A **mini programming language** designed for one specific task.

```
rule "Family" where entity_name:c:"KANTI" assign category_id:1 priority 10;
```

Instead of writing Python code, users write simple rules in a readable format.

---

## AST (Abstract Syntax Tree)

The **structured representation** of that DSL after parsing.

```
DSL Text                          →    AST (Python objects)
─────────────────────────────────────────────────────────────
rule "Family" where               →    CategorizationRule(
  entity_name:c:"KANTI"                  name="Family",
assign category_id:1                     conditions=OrBlock([
priority 10;                               AndBlock([
                                             FilterExpression(
                                               field="entity_name",
                                               operator=ContainsOperator(["KANTI"])
                                             )
                                           ])
                                         ]),
                                         assignment=Assignment(category_id=1),
                                         priority=10
                                       )
```

---

## The Pipeline

```
DSL Text  →  Tokenizer  →  Tokens  →  Parser  →  AST  →  Evaluator  →  Result
   ↓            ↓            ↓          ↓         ↓          ↓
"rule..."    breaks      [RULE,     builds    Python    runs logic
             into        STRING,    tree      objects   against data
             pieces      WHERE...]  structure
```

**Why?**
- DSL = easy for humans to write
- AST = easy for code to process
