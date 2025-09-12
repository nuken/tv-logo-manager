# **TV Logo Manager V2**

A robust, self-hosted Dockerized application designed to streamline the management of TV channel logo images using **Cloudinary** for cloud-based storage and delivery.

## **✨ Features**

- **Cloudinary Integration:** Automatically uploads processed logos to your Cloudinary account for reliable, fast, and scalable hosting.
- **Effortless Uploads:** Easily upload single or multiple image files through a user-friendly web interface.
- **Automated Image Processing:** All uploaded images are automatically **resized to a consistent 4:3 aspect ratio (720x540px)** with padding and converted to the universally compatible **PNG format**.
- **Interactive Logo Gallery:** View all your uploaded logos in a clean, responsive grid.
- **Direct Access Links:** Each logo provides an easy-to-copy, secure Cloudinary URL, perfect for M3U8 playlists.
- **Simple Management:** Delete unwanted logos from the system and your Cloudinary account with a single click.
- **Persistent Metadata:** Logo metadata is stored in a persistent Docker volume.

## **🚀 Getting Started**

### **Prerequisites**

1.  **Docker:** Ensure you have **Docker Desktop** (Windows/macOS) or **Docker Engine** (Linux) installed.
2.  **Cloudinary Account:** You will need a free Cloudinary account.
    * Sign up at [cloudinary.com](https://cloudinary.com/users/register/free).
    * After signing up, navigate to your **Dashboard**. You will find your **Cloud Name**, **API Key**, and **API Secret** here. You will need these for the next step.

### **Running the Application**

1.  **Create a Docker Volume (once):**
    This volume will persistently store your logo metadata.
    ```bash
    docker volume create tv-logo-data
    ```

2.  **Run the Docker Container:**
    Use the following command to start the container. **Replace the placeholder values** with your actual Cloudinary credentials from your dashboard.

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

    - `-e CLOUDINARY_CLOUD_NAME`: **(Required)** Your Cloudinary account's Cloud Name.
    - `-e CLOUDINARY_API_KEY`: **(Required)** Your Cloudinary account's API Key.
    - `-e CLOUDINARY_API_SECRET`: **(Required)** Your Cloudinary account's API Secret.

3.  **Access the Application:**
    Once the container is running, open your web browser and navigate to: **http://localhost:8084**

You can now start uploading your TV logos!
