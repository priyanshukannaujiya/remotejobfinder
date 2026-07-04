FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright browsers and their system dependencies in one layer
RUN playwright install chromium && \
    playwright install-deps chromium && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . .

# Run the APScheduler
CMD ["python", "main.py"]
