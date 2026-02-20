FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY frontend.py .

# Run as non-root user
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "main:app"]
