# Use the latest official Python image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Install required system dependencies (Piper dependencies)
RUN apt-get update && apt-get install -y \
    libopenblas-dev libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the project files into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Piper is executable (if included)
RUN chmod +x piper

# Run the script when the container starts
CMD ["python", "sx_test.py"]
