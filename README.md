# TV Logo Manager

A self-hosted Dockerized application to upload, manage, and serve TV channel logo images. This tool allows users to upload logos, which are automatically processed to a 4:3 aspect ratio and converted to optimized WebP format. It features a web interface for uploading, viewing, re-uploading, and deleting logos, with persistent storage.

## Features

* **Upload Logos:** Easily upload single or multiple TV channel logo images.
* **Automatic Processing:** Images are automatically converted to 4:3 aspect ratio (using padding to avoid cropping) and optimized WebP format for fast loading and reduced size.
* **Logo Gallery:** View all uploaded logos in a clean, responsive grid.
* **Direct Links:** Get direct URLs for each logo to use in custom M3U8 playlists or other applications.
* **Reupload & Delete:** Update existing logos or remove them from the system.
* **Persistent Storage:** Data (images and metadata) is stored persistently using Docker volumes.

## Getting Started

### Prerequisites

* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/macOS) or [Docker Engine](https://docs.docker.com/engine/install/) (Linux) installed and running.
* [Git](https://git-scm.com/downloads) installed.

### Setup and Running

I will update this readme tomorrow. Here is the Docker Run to get it going

``` docker run -d --restart unless-stopped --name logo-manager -p 8084:8084 -v tv-logo-data:/app/data rcvaughn2/tv-logo-manager ```

More Coming Soon