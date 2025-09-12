# tv-logo-manager/Dockerfile
# Use a lightweight official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Set environment variables for Cloudinary credentials
ENV CLOUDINARY_CLOUD_NAME=""
ENV CLOUDINARY_API_KEY=""
ENV CLOUDINARY_API_SECRET=""

# Copy the requirements file into the container at /app
COPY requirements.txt .
# Install any needed Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container at /app
# This copies app.py
COPY app.py .
# Create the data directory for persistent storage.
RUN mkdir -p data/images

# Make port 8084 available to the outside world
EXPOSE 8084

# Define the command to run when the container launches
CMD ["python", "app.py"]