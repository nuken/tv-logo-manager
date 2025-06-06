## **TV Logo Manager**

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
  ```
  docker volume create tv-logo-data
  ```
  
3. Run the Docker Container:  
  Use the following command to start the TV Logo Manager container in detached mode, with automatic restart, a specific name, port mapping, and data persistence via the Docker volume:  
  ```
  docker run \-d \--restart unless-stopped \--name logo-manager \-p 8084:8084 \-v tv-logo-data:/app/data rcvaughn2/tv-logo-manager
  ```
  
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

## **🔒 Remote Access with Tailscale (No Port Forwarding!)**

For users who want to access their TV Logo Manager and the hosted images from their personal devices *away from home* without the complexities and security risks of port forwarding, **Tailscale** is the recommended solution. Tailscale creates a secure, private network (a "tailnet") between your devices, allowing them to communicate as if they were on the same local network, wherever they are in the world.

### How Tailscale Works for You:

- **Zero Configuration:** No need to touch your router or firewall settings.
  
- **Secure:** All traffic is encrypted with WireGuard, ensuring your access is private.
  
- **Personal Use:** Ideal for accessing your own self-hosted services from your laptop, phone, or other devices when you're not at home.
  

### 1. Setting Up Tailscale on Your Docker Host (Server)

This is the computer where your `logo-manager` Docker container is running.

1. **Install Tailscale:**
  
  - Go to the [Tailscale Download Page](https://tailscale.com/download "null") and download the appropriate client for your Docker host's operating system (Windows, macOS, Linux).
    
  - Follow the installation instructions for your OS. For Linux, there's usually a simple command-line setup.
    
2. **Log In:**
  
  - Once installed, open the Tailscale application and log in using your chosen identity provider (Google, Microsoft, GitHub, etc.). This enrolls your Docker host into your private Tailscale network (your "tailnet").
3. **Note Your Tailscale IP:**
  
  - After logging in, Tailscale will assign a private IP address to your Docker host (e.g., `100.X.Y.Z`). You can find this IP in the Tailscale application or on your [Tailscale Admin Console](https://login.tailscale.com/admin/machines "null"). **Make a note of this IP address.**

Your Docker host is now securely part of your tailnet and accessible via its Tailscale IP.

### 2. Accessing the TV Logo Manager UI (for Admin/Management)

From any of your personal devices (laptop, phone, tablet) that also has Tailscale installed:

1. **Install & Log In to Tailscale:** Just like your Docker host, install the Tailscale app on your personal device and log in with the *same Tailscale account*.
  
2. **Connect to Your Tailnet:** Ensure the Tailscale app on your device shows it's connected (e.g., by the "on" toggle).
  
3. **Open the Web Interface:** In your device's web browser, navigate to:
  
  ```
  http://<Your_Docker_Host_Tailscale_IP>:8084
  ```
  
  (Replace `<Your_Docker_Host_Tailscale_IP>` with the `100.X.Y.Z` address you noted earlier).
  

You will now be able to access the TV Logo Manager's web interface securely, just as if you were on your home network. From here, you can upload new logos, manage existing ones, and **copy the direct image links**. The links provided by the "Copy Link" button in the UI will automatically use the correct IP address (which will be your Docker host's Tailscale IP, e.g., `http://100.X.Y.Z:8084/images?id=XXX`).

### 3. Using Logo Images on Client Devices (TVs, Phones, etc.)

**This is the crucial step for using the logo images in your M3U8 playlists or other applications.**

**Any device that needs to display or use the logo URLs generated by your TV Logo Manager (e.g., a TV app playing a custom M3U8 playlist, a media player on your phone, another computer) must also be running the Tailscale client and connected to your tailnet.**

1. **Install Tailscale on the Client Device:**
  
  - Go to the [Tailscale Download Page](https://tailscale.com/download "null").
    
  - Find the Tailscale client for your specific device type (e.g., Android TV, iOS, Android phone, Windows, Linux, Fire TV).
    
  - Follow the installation instructions.
    
2. **Log In (Same Account):**
  
  - Open the Tailscale app on that device and log in using the *same Tailscale account* as your Docker host.
3. **Ensure Connection:** Verify the Tailscale app is running and connected.
  
4. **Use the Tailscale IP in M3U8 Playlists:**
  
  - When you create or edit your M3U8 playlists, the logo URLs should reference your Docker host's Tailscale IP. For example, a line in your M3U8 might look like:
    
    ```
    #EXTINF:-1 tvg-id="CNN" tvg-logo="http://100.X.Y.Z:8084/images?id=123" group-title="News",CNN
    ```
    
    (Again, replace `100.X.Y.Z` with your actual Docker Host's Tailscale IP).
    

**Important Note on Device Compatibility:** While Tailscale supports a wide range of operating systems, some very locked-down smart TVs or streaming devices might not have a native Tailscale app available. In such rare cases, you might need an intermediary device (like a Raspberry Pi acting as a [Tailscale Subnet Router](https://tailscale.com/kb/1019/subnet-routers/ "null") or [Exit Node](https://tailscale.com/kb/1103/exit-nodes/ "null")) to route traffic for non-Tailscale-compatible devices on your home network, but this is a more advanced setup. For most common personal devices (phones, tablets, PCs, Android-based TVs/boxes), a direct Tailscale client installation is usually possible.

By following these steps, you create a private, secure network for your TV Logo Manager and all your personal devices, allowing you to access your images seamlessly from anywhere without exposing your home network to the public internet.

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
