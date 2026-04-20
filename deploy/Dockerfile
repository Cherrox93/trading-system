FROM python:3.11-slim

WORKDIR /app

# Systemowe zależności
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    git \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Python zależności (cache layer)
COPY deploy/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kod źródłowy
COPY . .

# Katalogi runtime
RUN mkdir -p database data logs knowledge_base/strategies

EXPOSE 8000

CMD ["python", "main.py"]
