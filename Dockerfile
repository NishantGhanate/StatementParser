FROM python:3.13

WORKDIR /app

# RUN pip install fastapi uvicorn pdfplumber python-multipart

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
