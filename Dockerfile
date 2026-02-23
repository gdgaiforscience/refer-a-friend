FROM python:3.12-slim

WORKDIR /app

# Install nginx
RUN apt-get update && apt-get install -y --no-install-recommends nginx && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY frontend.py .
COPY Beaker_Icon.png .
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Remove the default nginx site
RUN rm -f /etc/nginx/sites-enabled/default

EXPOSE 8080

# Start nginx, FastAPI, and Streamlit
CMD sh -c "nginx && uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1 & streamlit run frontend.py --server.port 8501 --server.address 127.0.0.1 --server.headless true"
