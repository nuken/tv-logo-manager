**TV Logo Manager**

A robust, self-hosted Dockerized application designed to streamline the management of TV channel logo images. This tool simplifies the process of uploading, processing, and serving logos for use in custom M3U8 playlists or other media applications.

## **✨ Features**

- **Effortless Uploads:** Easily upload single or multiple image files through a user-friendly web interface.
- **Automated Image Processing:** All uploaded images are automatically resized to a consistent **4:3 aspect ratio** (using padding to ensure no part of your logo is ever cut off) and converted to highly optimized **WebP format** for superior performance and reduced storage footprint.
- **Interactive Logo Gallery:** View all your uploaded logos in a clean, responsive grid layout directly within the web interface.
- **Direct Access Links:** Each logo in the gallery provides an easy-to-copy direct URL (http://\<docker\_ip\>:8084/images?id=XXX), perfect for integrating with your M3U8 playlists.
- **Management Options:** Reupload new versions of existing logos or delete them from the system with a single click.
- **Persistent Storage:** All uploaded images and their metadata are stored persistently, ensuring your data is safe even if the Docker container is stopped or restarted.

## **🚀 Getting Started**

This guide will help you get the TV Logo Manager up and running quickly using Docker.

### **Prerequisites**

Before you begin, ensure you have the following installed:

- **Docker Desktop** (for Windows or macOS) or **Docker Engine** (for Linux).

### **Running the Application**

The easiest way to get started is by pulling the pre-built Docker image from Docker Hub.

1. Create a Docker Volume (once):  
  This volume will store your uploaded logos and application data persistently, even if the container is removed.  
  ```docker volume create tv-logo-data```
  
2. Run the Docker Container:  
  Use the following command to start the TV Logo Manager container in detached mode, with automatic restart, a specific name, port mapping, and data persistence via the Docker volume:  
  ```docker run \-d \--restart unless-stopped \--name logo-manager \-p 8084:8084 \-v tv-logo-data:/app/data rcvaughn2/tv-logo-manager```
  
  - \-d: Runs the container in **detached mode** (in the background).
  - \--restart unless-stopped: The container will automatically restart unless it's explicitly stopped or Docker is stopped.
  - \--name logo-manager: Assigns a human-readable name to your container (logo-manager).
  - \-p 8084:8084: Maps port 8084 on your host machine to port 8084 inside the container.
  - \-v tv-logo-data:/app/data: Mounts the named Docker volume tv-logo-data to the /app/data directory inside the container, ensuring data persistence.
  - rcvaughn2/tv-logo-manager: The name of the Docker image to pull and run from Docker Hub.
3. Access the Application:  
  Once the container is running, open your web browser and navigate to:  
  http://\<docker\_ip\>:8084
  
  You should see the TV Logo Manager interface ready for you to upload and manage your logos\!
  

## **🛠️ Local Development (for Contributors)**

If you wish to modify the source code or build the image yourself:

1. **Clone the Repository:**  
  git clone https://github.com/nuken/tv-logo-manager.git  
  cd tv-logo-manager
  
2. **Build the Docker Image Locally:**  
  docker build \-t tv-logo-manager .
  
3. Run the Local Image:  
  You can then run your locally built image (with a bind mount for easy local development data access):  
  docker run \-p 8084:8084 \-v "$(pwd)/data:/app/data" tv-logo-manager
  
  *(On Windows, ensure $(pwd) resolves correctly or use your full path like C:/Users/YourUser/tv-logo-manager/data.)*
  

## **📂 Project Structure**

tv-logo-manager/  
├── .github/ \# GitHub Actions workflows  
│ └── workflows/  
│ └── build-and-push.yml \# Workflow to build and push Docker image to Docker Hub  
├── data/ \# Persistent data (managed by Docker volume/bind mount)  
│ ├── images/ \# Stores processed WebP logo images  
│ └── logos.json \# Simple JSON database for logo metadata  
├── app.py \# Flask backend application with integrated HTML/JS frontend  
├── Dockerfile \# Instructions for building the Docker image  
├── requirements.txt \# Python dependencies (Flask, Pillow)  
├── .gitignore \# Specifies files/folders to exclude from Git tracking  
└── README.md \# This project documentation

##
