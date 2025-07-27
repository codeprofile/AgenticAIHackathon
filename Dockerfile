# Use full Python base image to support reportlab dependencies
FROM python:3.12

# Set working directory
WORKDIR /app

# Install only necessary system dependencies for reportlab
RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy all project files
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Run the FastAPI app
CMD ["unicorn", "main:app", "--host". "0.0.0.0",  "--port", "8000"]

