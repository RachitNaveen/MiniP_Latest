# Use an official Python runtime as a parent image
# You can adjust the Python version if needed, e.g., python:3.13-slim if all dependencies are compatible
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies required for face-recognition, dlib, and opencv-python
# Also install git for installing face_recognition_models from a git repository
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libopenblas-dev \
    liblapack-dev \
    libjpeg-dev \
    libpng-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install/upgrade setuptools first, as it's needed by face_recognition_models
RUN pip install --no-cache-dir --upgrade setuptools

# Install face_recognition_models from its git repository
# This is done before requirements.txt in case face-recognition (in requirements.txt)
# needs this specific version of models.
RUN pip install --no-cache-dir git+https://github.com/ageitgey/face_recognition_models

# Copy requirements.txt first to leverage Docker's layer caching
COPY requirements.txt .

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
# This includes your 'app' directory, 'run.py', 'config.py', etc.
# IMPORTANT: Ensure your 'app/static/face-api-models/' directory with the .weights files
# exists in your project before building the image, so it gets copied here.
COPY . .

# Create the instance directory for the SQLite database if it doesn't exist.
# The db.create_all() in run.py will create the database file.
# For data persistence across container restarts, mount a volume to /app/instance.
RUN mkdir -p /app/instance

# Expose the port the app runs on (Flask default is 5000)
EXPOSE 5000

# The command to run your application
# Your run.py script handles db.create_all() and starts the Flask-SocketIO server
CMD ["python", "run.py"]