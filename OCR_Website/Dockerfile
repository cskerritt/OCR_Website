FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ghostscript \
    tesseract-ocr \
    unpaper \
    pngquant \
    qpdf \
    liblept5 \
    libmagic1 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create the uploads, cache, and instance directories
RUN mkdir -p uploads ocr_cache instance && chmod 777 uploads ocr_cache instance

# Create a non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables for production
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "300", "app:app"]