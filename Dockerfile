# Dockerfile
FROM python:3.9-slim

# Set up working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script
COPY app.py app.py

# Set the command to run the Python script
CMD ["python", "app.py"]
