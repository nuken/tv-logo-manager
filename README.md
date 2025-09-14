# **TV Logo Manager** V2.1.1

A robust, self-hosted Dockerized application designed to streamline the management of TV channel logo images using **Cloudinary** for cloud-based storage and delivery.

## **✨ Features**

- **Flexible Configuration:** Set your Cloudinary credentials via environment variables (recommended for Docker) or through a one-time web-based setup form.
- **Cloudinary Integration:** Automatically uploads processed logos to your Cloudinary account.
- **Local Image Caching:** Images are cached locally after the first view to reduce bandwidth usage and speed up gallery loading.
- **Clear Cache:** A simple button to clear the local image cache, forcing the app to re-download fresh copies from Cloudinary.
- **Local Backup:** Download a zip archive of all your hosted logos with a single click.
- **Automated Image Processing:** All uploaded images are automatically resized to a **4:3 aspect ratio (720x540px)** and converted to **PNG format**.
- **Interactive Logo Gallery:** View, manage, and copy links for all your uploaded logos.
- **Persistent Storage:** Logo, configuration, and cached image data are stored in a persistent Docker volume.

## **🚀 Getting Started**

### **Prerequisites**

1.  **Docker:** Ensure you have **Docker Desktop** (Windows/macOS) or **Docker Engine** (Linux) installed.
2.  **Cloudinary Account:** You will need a free Cloudinary account to get your **Cloud Name**, **API Key**, and **API Secret** from the dashboard.

### **Running the Application**

1.  **Create a Docker Volume:**
    This volume will persistently store your configuration and logo metadata.
    ```bash
    docker volume create tv-logo-data
    ```

2.  **Run the Docker Container:**
    You have two options for configuration. Using environment variables is the recommended method.

    **Option A: Configure with Environment Variables (Recommended)**
    Provide your credentials directly in the `docker run` command. This is ideal for automated setups.

    ```bash
    docker run -d \
      --restart unless-stopped \
      --name logo-manager \
      -p 8084:8084 \
      -v tv-logo-data:/app/data \
      -e CLOUDINARY_CLOUD_NAME='YOUR_CLOUD_NAME' \
      -e CLOUDINARY_API_KEY='YOUR_API_KEY' \
      -e CLOUDINARY_API_SECRET='YOUR_API_SECRET' \
      rcvaughn2/tv-logo-manager
    ```

    **Option B: Configure with the Web Form**
    If you prefer not to use environment variables, simply run the container without them.
    ```bash
    docker run -d \
      --restart unless-stopped \
      --name logo-manager \
      -p 8084:8084 \
      -v tv-logo-data:/app/data \
      rcvaughn2/tv-logo-manager
    ```
    Then, open your web browser to **http://localhost:8084**. You will be automatically redirected to a setup page to enter and save your credentials.

You can now start uploading your TV logos!