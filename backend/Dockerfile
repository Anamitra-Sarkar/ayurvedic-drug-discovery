FROM python:3.10-slim

WORKDIR /app

# Install system deps for RDKit, Vina optional
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxrender1 libxext6 libsm6 libx11-6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Optional: install Vina if conda not available, fallback mock used
# RUN apt-get install -y autodock-vina || echo "Vina not in apt, using mock"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
