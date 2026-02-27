# Start with a lightweight Python environment
FROM python:3.10-slim

# Install FFmpeg (Crucial for video processing)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app code
COPY . .

# Run the app using gunicorn for production stability
CMD gunicorn --bind 0.0.0.0:$PORT app:app
