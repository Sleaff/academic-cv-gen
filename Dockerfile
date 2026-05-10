FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure the entrypoint script is executable
RUN chmod +x entrypoint.sh

# Expose both ports
EXPOSE 8000 8501

# Run the entrypoint script
CMD ["./entrypoint.sh"]