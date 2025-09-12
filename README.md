# **TV Logo Manager**
V2.1

A robust, self-hosted Dockerized application designed to streamline the management of TV channel logo images using **Cloudinary** for cloud-based storage and delivery.

## **✨ Features**

- **Easy Web-Based Setup:** Configure your Cloudinary credentials through a simple web form after the first launch.
- **Cloudinary Integration:** Automatically uploads processed logos to your Cloudinary account.
- **Local Backup:** Download a zip archive of all your hosted logos with a single click.
- **Automated Image Processing:** All uploaded images are automatically resized to a **4:3 aspect ratio (720x540px)** and converted to **PNG format**.
- **Interactive Logo Gallery:** View, manage, and copy links for all your uploaded logos.
- **Persistent Storage:** Logo and configuration data are stored in a persistent Docker volume.

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
    This command is now much simpler, as no credentials are required at startup.
    ```bash
    docker run -d \
      --restart unless-stopped \
      --name logo-manager \
      -p 8084:8084 \
      -v tv-logo-data:/app/data \
      rcvaughn2/tv-logo-manager
    ```

3.  **First-Time Setup:**
    * Open your web browser and navigate to **http://localhost:8084**.
    * You will be automatically redirected to the setup page.
    * Enter your Cloudinary `Cloud Name`, `API Key`, and `API Secret` and click "Save".

You will then be taken to the main application and can start uploading your TV logos!