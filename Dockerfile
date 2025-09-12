# tv-logo-manager/Dockerfile
# Use a lightweight official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .
# Install any needed Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application and the static folder
COPY app.py .
COPY static /app/static

# Create the data directory for persistent storage.
RUN mkdir -p data/images

# Make port 8084 available to the outside world
EXPOSE 8084

# Define the command to run when the container launches
CMD ["python", "app.py"]