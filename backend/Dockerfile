FROM python:3.12-slim

WORKDIR /app

# Set environment variables to prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED 1

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# The command to run will be specified in the docker-compose.yml
# This allows us to use the same image for different services (api vs worker)