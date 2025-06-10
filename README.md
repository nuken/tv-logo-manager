# **TV Logo Manager**

A robust, self-hosted Dockerized application designed to streamline the management of TV channel logo images. This tool simplifies the process of uploading, **processing**, and serving logos for use in custom M3U8 playlists or other media applications.

## **✨ Features**

- **Effortless Uploads:** Easily upload single or multiple image files through a user-friendly web interface.
- **Automated Image Processing:** All uploaded images are automatically **resized to a consistent 4:3 aspect ratio** (using padding to ensure no part of your logo is ever cut off) and converted to highly optimized **WebP format** for superior performance and reduced storage footprint.
- **Interactive Logo Gallery:** View all your uploaded logos in a clean, responsive grid layout directly within the web interface.
- **Direct Access Links:** Each logo in the gallery provides an easy-to-copy direct URL (`http://<docker_ip>:8084/images?id=XXX`), perfect for integrating with your M3U8 playlists.
- **Download Options:** **Download your processed logos in either WebP or universally compatible PNG formats** with a single click.
- **Management Options:** Delete unwanted logos from the system with a single click.
- **Persistent Storage:** All uploaded images and their metadata are stored persistently, ensuring your data is safe even if the Docker container is stopped or restarted.

## **🚀 Getting Started**

This guide will help you get the TV Logo Manager up and running quickly using Docker.

### **Prerequisites**

Before you begin, ensure you have the following installed:

- **Docker Desktop** (for Windows or macOS) or **Docker Engine** (for Linux).

### **Running the Application**

The easiest way to get started is by pulling the pre-built Docker image from Docker Hub.

**Create a Docker Volume (once):** This volume will store your uploaded logos and application data persistently, even if the container is removed.  

```
docker volume create tv-logo-data
```

1. **Run the Docker Container:** Use the following command to start the TV Logo Manager container in detached mode, with automatic restart, a specific name, port mapping, and data persistence via the Docker volume:  
 
  ```
  docker run -d --restart unless-stopped --name logo-manager -p 8084:8084 -v tv-logo-data:/app/data rcvaughn2/tv-logo-manager
  ```
  
2. - `-d`: Runs the container in **detached mode** (in the background).
  - `--restart unless-stopped`: The container will automatically restart unless it's explicitly stopped or Docker is stopped.
  - `--name logo-manager`: Assigns a human-readable name to your container (`logo-manager`).
  - `-p 8084:8084`: Maps port 8084 on your host machine to port 8084 inside the container.
  - `-v tv-logo-data:/app/data`: Mounts the named Docker volume `tv-logo-data` to the `/app/data` directory inside the container, ensuring data persistence.
  - `rcvaughn2/tv-logo-manager`: The name of the Docker image to pull and run from Docker Hub.

**Access the Application:** Once the container is running, open your web browser and navigate to:  
http://localhost:8084

3. You should see the TV Logo Manager interface ready for you to upload and manage your logos\!
  
## **📺 Integrating with Channels DVR**

The TV Logo Manager is an excellent companion for Channels DVR, allowing you to easily process and prepare logo images for use in your custom M3U8 playlists. Since Channels DVR manages its own image hosting, this process involves two steps: preparing the image with the TV Logo Manager, and then uploading it to Channels DVR.

1. **Prepare & Download the PNG Logo:**  
   * **Upload** your original logo image to the TV Logo Manager via its web interface (http://localhost:8084). The manager will automatically process it to the **4:3 aspect ratio** and optimize it.  
   * Locate the newly uploaded logo in the gallery and click the **"Download PNG"** button. This will download the processed image, typically named based on its original filename (e.g., MyChannelLogo.png), which is the format Channels DVR prefers.  
2. **Upload to Channels DVR Image Manager:**  
   * Open your Channels DVR web interface (typically http://\<Channels\_DVR\_IP\>:8089/admin).  
   * Navigate to **DVR** \-\> **Manage** \-\> **Images**.  
   * Click the **"Upload Image"** option.  
   * Select the PNG file you downloaded in Step 1 from your computer and upload it.  
   * After the upload, Channels DVR will display the image and provide its internal URL in the Image Manager. This URL typically looks like /dvr/uploads/\[YOUR IMAGE ID\]/content or similar. **Make a note of the exact URL Channels DVR generates for your image.**  
3. **Use the Internal Link in Your M3U8 Playlist:**  
   * In your custom M3U8 playlist, use the internal Channels DVR URL format for the tvg-logo attribute. This ensures Channels DVR serves the logo directly from its own server, which is generally more stable for its internal operations.  
   * **Example M3U8 Entry:**  
     `#EXTINF:-1 tvg-id="MyChannel" tvg-logo="/dvr/uploads/YOUR_IMAGE_ID/content" group-title="My Group",My Awesome Channel`  
     (Replace YOUR\_IMAGE\_ID with the actual ID or path segment Channels DVR provided for your uploaded logo).

This workflow ensures your logos are perfectly sized and formatted for Channels DVR while leveraging its native image hosting.


## **🔒 Remote Access with Tailscale**

For users who want to access their TV Logo Manager and the hosted image links from their personal devices *away from home* without the complexities and security risks of traditional port forwarding, **Tailscale** offers a straightforward solution. Tailscale creates a secure, private network between your devices, allowing them to communicate as if they were on the same local network, wherever they are in the world.

### **How it Works for You:**

- **Easy Setup:** Install Tailscale on your Docker host and your personal devices, then log into the same Tailscale account.
- **Secure Access:** Your devices can then communicate securely over Tailscale's private IP addresses.
- **Remote Link Usage:** This allows you to use the generated image links (e.g., `http://<Your_Docker_Host_Tailscale_IP>:8084/images?id=XXX`) in your M3U8 playlists or other applications on your personal devices, even when you're away from your home network.

## **🛠️ Local Development (for Contributors)**

If you wish to modify the source code or build the image yourself:

**Clone the Repository:**  
git clone https://github.com/nuken/tv-logo-manager.git  
cd tv-logo-manager

1. **Build the Docker Image Locally:**  
  docker build \-t tv-logo-manager .
  

**Run the Local Image:** You can then run your locally built image (with a bind mount for easy local development data access):  
docker run \-p 8084:8084 \-v "$(pwd)/data:/app/data" tv-logo-manager

3. *(On Windows, ensure `$(pwd)` resolves correctly or use your full path like `C:/Users/YourUser/tv-logo-manager/data`.)*
  

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
