# Statement Parser

A FastAPI application to parse bank statement PDFs and extract transaction data.
Supports multiple Indian banks with automatic bank detection and transaction categorization.

## Features

- 📄 Parse bank statement PDFs using pdfplumber
- 🏦 Auto-detect bank from email sender or PDF content
- 💰 Extract transactions with date, amount, balance, and entity details
- 🔍 Identify payment methods (UPI, NEFT, IMPS, RTGS, etc.)
- 👤 Extract entity/person names from transaction descriptions
- 📊 Extract account details (number, IFSC, type)
- ⚡ Async processing with Celery workers

## Supported Banks

- [x] Union Bank of India
- [] Kotak Mahindra Bank
- [] State Bank of India (SBI)
- [] HDFC Bank
- [] ICICI Bank
- [] Axis Bank

## Tech Stack

- **Backend:** FastAPI, Python 3.12
- **PDF Parsing:** pdfplumber
- **Task Queue:** Celery with Redis
- **Database:** Shared PostgreSQL
- **Containerization:** Docker

## Installation

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis

### Local Setup
```bash
# Clone repository
git clone https://github.com/NishantGhanate/StatementParser.git
cd StatementParser

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# [OPTIONAL] Run migrations
python -m alembic upgrade head

# Start the application
uvicorn app.main:app --reload
```

## VISTI ME
> http://localhost:8000/docs

### Docker Setup
```bash
# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Configuration

Create a `.env` file with the following variables:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/statement_parser

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API
API_PORT=8000
```

## Usage

### Parse a Bank Statement
```python
from app.parsers import parse_statement
from app.parsers.base import BankName

result = parse_statement(pdf_path="statement.pdf", bank_name=BankName.UNION)
print(result)
```

### API Endpoints
```bash
# Upload and parse statement
POST /api/v1/statements/upload
Content-Type: multipart/form-data

# Get parsed transactions
GET /api/v1/statements/{statement_id}/transactions

# Get account details
GET /api/v1/accounts/{account_id}
```

### CLI Usage
```bash
python app/tasks/bank_statement_upload.py --input files/statement.pdf --from_email noreply@unionbankofindia.bank.in
```



## Database
```sql

```

## Running Celery Workers
```bash
# Start worker
celery -A app.celery_app worker --loglevel=info -Q statment_parser

# Start beat scheduler
celery -A app.celery_app beat --loglevel=info
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-bank`)
3. Commit changes (`git commit -am 'Add new bank parser'`)
4. Push to branch (`git push origin feature/new-bank`)
5. Open a Pull Request



## License

MIT License
