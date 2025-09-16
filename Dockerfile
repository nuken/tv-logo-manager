# tv-logo-manager/Dockerfile
# Use a lightweight official Python runtime as a parent image
FROM python:3.13-slim-bookworm

# Set the working directory inside the container
WORKDIR /app

# Set environment variables for Cloudinary credentials as an option
ENV CLOUDINARY_CLOUD_NAME=""
ENV CLOUDINARY_API_KEY=""
ENV CLOUDINARY_API_SECRET=""

# Copy the requirements file into the container at /app
COPY requirements.txt .
# Install any needed Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application and the static folder
COPY app.py .
COPY static /app/static

# Create the data and cache directories for persistent storage.
RUN mkdir -p data/images data/cache

# Make port 8084 available to the outside world
EXPOSE 8084

# Define the command to run when the container launches using Gunicorn
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8084", "app:app"]