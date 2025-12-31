# StatementParser

StatementParser is a Python-based system for parsing bank statement PDFs, extracting **transactions and metadata**, enriching transactions using a **rule engine via a transaction adapter**, and persisting everything into PostgreSQL with proper foreign-key relationships.

---

## Features

- Canonical PDF full-text extraction
- Transaction table parsing from PDFs
- Bank-specific metadata extraction (currently Union Bank of India)
- **Transaction Adapter layer** to connect parsed data with the Rule Engine
- Rule Engine–based enrichment (credit/debit, payment method, category, tags)
- PostgreSQL persistence with FK linking (`statement_id`)
- Idempotent inserts (safe re-runs)

---

## Current Support

- **Bank**: Union Bank of India  
- **Metadata Extracted**:
  - Account holder name
  - Account number
  - Account type
  - CIF ID
  - Currency
- **Data Stored**:
  - Statement metadata (`bank_info`)
  - Transactions linked via `statement_id`

---


---

## Data Flow

1. PDF uploaded
2. Full text extracted (canonical extractor)
3. Transactions parsed from tables
4. Metadata extracted from full text
5. **Transactions passed through `transaction_adapter`**
6. Rule engine enriches transactions
7. Metadata saved to `bank_info`
8. Transactions saved to `bank_transactions` with `statement_id` FK

---

## Database Model (Core)

- **bank_info**
  - One row per account
  - Unique on `account_number`
- **bank_transactions**
  - Multiple rows per account
  - Linked using `statement_id → bank_info.id`

---

## How to Run

```bash
source venv/bin/activate
source .env

python -m app.tasks.bank_statement_upload \
  --input union1.pdf \
  --from_email noreplyunionbankofindia@unionbankofindia.bank.in


