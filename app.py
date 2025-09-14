# tv-logo-manager/app.py
from flask import Flask, request, jsonify, redirect, send_file, Response, render_template_string, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename
import json
from PIL import Image, ImageOps
import io
import cloudinary
import cloudinary.uploader
import cloudinary.api
import sys
import requests
import zipfile

app = Flask(__name__)
__version__ = "2.1.1"

# --- Configuration ---
UPLOAD_FOLDER = 'data/images'
CACHE_FOLDER = 'data/cache'
DB_FILE = 'data/logos.json'
CONFIG_FILE = 'data/config.json'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CACHE_FOLDER'] = CACHE_FOLDER

# --- Ensure Data Directories Exist on Startup ---
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)

# --- Cloudinary Configuration ---
def load_cloudinary_config():
    """
    Loads Cloudinary config, prioritizing environment variables over the config file.
    Returns the config dictionary if successful, otherwise None.
    """
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key = os.getenv('CLOUDINARY_API_KEY')
    api_secret = os.getenv('CLOUDINARY_API_SECRET')

    config = None

    # Priority 1: Environment Variables
    if all([cloud_name, api_key, api_secret]):
        config = {
            "CLOUDINARY_CLOUD_NAME": cloud_name,
            "CLOUDINARY_API_KEY": api_key,
            "CLOUDINARY_API_SECRET": api_secret
        }
    # Priority 2: Config File
    elif os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                file_config = json.load(f)
                if all(file_config.get(k) for k in ["CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"]):
                    config = file_config
            except (json.JSONDecodeError, KeyError):
                pass  # Ignore invalid config file

    if config:
        cloudinary.config(
            cloud_name=config.get('CLOUDINARY_CLOUD_NAME'),
            api_key=config.get('CLOUDINARY_API_KEY'),
            api_secret=config.get('CLOUDINARY_API_SECRET')
        )
        return config
    
    return None

# --- Helper Functions for Data Storage (Simple JSON DB) ---
def load_logos():
    """Loads logo metadata from the JSON file."""
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_logos(logos):
    """Saves logo metadata to the JSON file."""
    with open(DB_FILE, 'w') as f:
        json.dump(logos, f, indent=4)

# --- Image Processing Function ---
def process_logo_image(image_path):
    """Processes an image to a 720x540 PNG with padding."""
    img = Image.open(image_path).convert("RGBA")
    target_size = (720, 540)
    padded_img = ImageOps.pad(img, target_size, color=(0, 0, 0, 0), centering=(0.5, 0.5))
    return padded_img

# --- Middleware to check for configuration ---
@app.before_request
def check_config():
    """Before each request, check if the app is configured."""
    if request.path.startswith(('/static/', '/cached-image/')) or request.endpoint in ['setup', 'favicon']:
        return
    if not load_cloudinary_config():
        return redirect(url_for('setup'))

# --- Flask Routes ---

@app.route('/favicon.ico')
def favicon():
    """Serves the favicon."""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/cached-image/<int:logo_id>')
def get_cached_image(logo_id):
    """Serves an image from the local cache, downloading it from Cloudinary if not present."""
    filename = f"{logo_id}.png"
    cache_path = os.path.join(app.config['CACHE_FOLDER'], filename)

    if os.path.exists(cache_path):
        return send_from_directory(app.config['CACHE_FOLDER'], filename)

    logos = load_logos()
    logo = next((l for l in logos if l.get('id') == logo_id), None)

    if not logo or not logo.get('url'):
        return "Image not found in database.", 404

    try:
        response = requests.get(logo['url'])
        response.raise_for_status()

        with open(cache_path, 'wb') as f:
            f.write(response.content)

        return send_from_directory(app.config['CACHE_FOLDER'], filename)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Failed to cache image ID {logo_id} from {logo['url']}: {e}")
        return redirect(logo['url'])

@app.route('/clear-cache')
def clear_cache():
    """Deletes all files in the local image cache directory."""
    cache_dir = app.config['CACHE_FOLDER']
    for filename in os.listdir(cache_dir):
        file_path = os.path.join(cache_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                app.logger.info(f"Removed cached file: {file_path}")
        except Exception as e:
            app.logger.error(f"Error deleting cache file {file_path}: {e}")
    return redirect(url_for('index'))

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Handles the initial setup of Cloudinary credentials."""
    if request.method == 'POST':
        config = {
            "CLOUDINARY_CLOUD_NAME": request.form['cloud_name'],
            "CLOUDINARY_API_KEY": request.form['api_key'],
            "CLOUDINARY_API_SECRET": request.form['api_secret']
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        load_cloudinary_config()
        return redirect(url_for('index'))

    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.ico') }}">
        <title>Setup TV Logo Manager</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f4f7f6; }
            .setup-container { background: #fff; padding: 40px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 400px; }
            h1 { text-align: center; color: #2c3e50; }
            form { display: flex; flex-direction: column; gap: 15px; }
            label { font-weight: bold; }
            input { padding: 10px; border-radius: 4px; border: 1px solid #ccc; }
            input[type="submit"] { background-color: #3498db; color: white; cursor: pointer; font-size: 1rem; }
        </style>
    </head>
    <body>
        <div class="setup-container">
            <h1>Cloudinary Setup</h1>
            <p>Please enter your Cloudinary credentials from your dashboard. (Note: Environment variables, if set, will override this form).</p>
            <form method="post">
                <label for="cloud_name">Cloud Name:</label>
                <input type="text" id="cloud_name" name="cloud_name" required>
                <label for="api_key">API Key:</label>
                <input type="text" id="api_key" name="api_key" required>
                <label for="api_secret">API Secret:</label>
                <input type="password" id="api_secret" name="api_secret" required>
                <input type="submit" value="Save Configuration">
            </form>
        </div>
    </body>
    </html>
    """)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles new image uploads, processes them, and uploads to Cloudinary."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    uploaded_files = request.files.getlist('file')
    if not uploaded_files or uploaded_files[0].filename == '':
        return jsonify({"error": "No files selected"}), 400

    results = []
    for file in uploaded_files:
        if file.filename == '':
            continue

        original_filename = secure_filename(file.filename)
        temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], "temp_" + original_filename)
        file.save(temp_filepath)

        try:
            processed_img = process_logo_image(temp_filepath)
            img_byte_arr = io.BytesIO()
            processed_img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            upload_result = cloudinary.uploader.upload(img_byte_arr, folder="tv-logos")
            os.remove(temp_filepath)

            logos = load_logos()
            new_id = max([l.get('id', 0) for l in logos]) + 1 if logos else 1
            logos.append({
                "id": new_id,
                "public_id": upload_result['public_id'],
                "original_name": original_filename,
                "url": upload_result['secure_url']
            })
            save_logos(logos)
            results.append({"message": "File uploaded", "id": new_id, "url": upload_result['secure_url']})
        except Exception as e:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            app.logger.error(f"Upload failed for {original_filename}: {e}")
            results.append({"error": f"Upload failed for {original_filename}: {e}"})

    status_code = 200 if any("message" in r for r in results) else 500
    return jsonify(results[0] if len(results) == 1 else results), status_code

@app.route('/api/logos', methods=['GET'])
def list_logos():
    """Returns a JSON list of all uploaded logo metadata."""
    logos = load_logos()
    return jsonify(sorted(logos, key=lambda x: x.get('id', 0)))

@app.route('/api/logos/<int:logo_id>', methods=['DELETE'])
def delete_logo(logo_id):
    """Deletes a logo by its ID from Cloudinary and the local cache."""
    logos = load_logos()
    logo_to_delete = next((logo for logo in logos if logo['id'] == logo_id), None)
    if not logo_to_delete:
        return jsonify({"error": "Logo not found"}), 404
        
    try:
        cloudinary.uploader.destroy(logo_to_delete['public_id'])
        cache_path = os.path.join(app.config['CACHE_FOLDER'], f"{logo_id}.png")
        if os.path.exists(cache_path):
            os.remove(cache_path)
        logos_after_deletion = [logo for logo in logos if logo['id'] != logo_id]
        save_logos(logos_after_deletion)
        return jsonify({"message": "Logo deleted"}), 200
    except Exception as e:
        app.logger.error(f"Delete failed for logo ID {logo_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/backup')
def backup_logos():
    """Creates and serves a zip archive of all logos."""
    logos = load_logos()
    if not logos:
        return "No logos to back up.", 404

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for logo in logos:
            try:
                url = logo['url']
                if '/upload/' in url:
                    parts = url.split('/upload/')
                    backup_url = parts[0] + '/upload/f_png/' + parts[1]
                else:
                    backup_url = url
                response = requests.get(backup_url)
                response.raise_for_status()
                base_name, _ = os.path.splitext(logo['original_name'])
                filename_in_zip = f"{logo['id']}_{base_name}.png"
                zf.writestr(filename_in_zip, response.content)
            except requests.exceptions.RequestException as e:
                app.logger.error(f"Could not download {logo['url']} for backup: {e}")
    
    memory_file.seek(0)
    return send_file(memory_file, download_name='tv_logos_backup.zip', as_attachment=True)

@app.route('/')
def index():
    """Serves the main HTML page."""
    template = """
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.ico') }}">
        <title>TV Logo Manager</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background-color: #f4f7f6; color: #333; }
            .container { max-width: 1000px; margin: 20px auto; background-color: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1); }
            h1, h2 { color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; margin-top: 30px; }
            #uploadForm { display: flex; flex-direction: column; gap: 15px; margin-bottom: 25px; padding: 20px; border: 1px dashed #bdc3c7; border-radius: 6px; background-color: #fcfcfc; }
            #fileInput { padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
            .button, input[type="submit"] { background-color: #3498db; color: white; border: none; padding: 12px 20px; border-radius: 4px; cursor: pointer; font-size: 1rem; text-decoration: none; display: inline-block; text-align: center; transition: background-color 0.2s ease; }
            .button.clear-cache { background-color: #e67e22; }
            .button:hover, input[type="submit"]:hover { background-color: #2980b9; }
            .button.clear-cache:hover { background-color: #d35400; }
            #uploadMessage { margin-top: 15px; padding: 10px; border-radius: 4px; display: none; }
            #uploadMessage.info { background-color: #e9ecef; color: #333; }
            #uploadMessage.success { background-color: #d4edda; color: #155724; }
            #uploadMessage.error { background-color: #f8d7da; color: #721c24; }
            #logoGallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; padding: 10px 0; }
            .logo-item { border: 1px solid #e0e0e0; padding: 15px; background-color: #f3f3f3; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); display: flex; flex-direction: column; align-items: center; text-align: center; min-width: 0; }
            .logo-item img { max-width: 100%; height: auto; max-height: 150px; border-radius: 4px; object-fit: contain; margin-bottom: 10px; }
            .logo-details { width: 100%; }
            .logo-details p { margin: 5px 0; font-size: 0.9rem; word-wrap: break-word; }
            .url-input { width: calc(100% - 16px); padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 0.8rem; background-color: #f7f7f7; cursor: text; }
            .actions { margin-top: 10px; display: flex; gap: 8px; justify-content: center; }
            .action-btn { background-color: #28a745; color: white; border: none; padding: 8px 12px; cursor: pointer; border-radius: 4px; font-size: 0.85rem; transition: background-color 0.2s ease; }
            .action-btn.delete { background-color: #dc3545; }
            .action-btn:hover { filter: brightness(1.1); }
            .header { display: flex; justify-content: space-between; align-items: center; }
            .header-actions { display: flex; gap: 10px; }
            .version-info { color: #7f8c8d; font-size: 0.9rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>TV Logo Manager</h1>
                <span class="version-info">Version: {{ version }}</span>
            </div>
            <div class="header-actions">
                <a href="/backup" class="button">Download Backup</a>
                <a href="/clear-cache" class="button clear-cache">Clear Image Cache</a>
            </div>
            <h2>Upload New Logo(s)</h2>
            <form id="uploadForm" enctype="multipart/form-data">
              <input type="file" name="file" id="fileInput" accept="image/*" multiple required>
              <input type="submit" value="Upload Logo(s)">
            </form>
            <div id="uploadMessage"></div>
            <h2>Uploaded Logos</h2>
            <div id="logoGallery"><p>Loading logos...</p></div>
        </div>
        <script>
            const uploadForm = document.getElementById('uploadForm');
            const fileInput = document.getElementById('fileInput');
            const uploadMessage = document.getElementById('uploadMessage');
            const logoGallery = document.getElementById('logoGallery');

            function showMessage(msg, type = 'info') {
                uploadMessage.textContent = msg;
                uploadMessage.className = type;
                uploadMessage.style.display = 'block';
                setTimeout(() => { uploadMessage.style.display = 'none'; }, 5000);
            }

            async function fetchLogos() {
                try {
                    logoGallery.innerHTML = '<p>Loading logos...</p>';
                    const response = await fetch('/api/logos');
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    const logos = await response.json();
                    logoGallery.innerHTML = logos.length === 0 ? '<p>No logos uploaded yet.</p>' : '';
                    logos.forEach(logo => {
                        const logoItem = document.createElement('div');
                        logoItem.className = 'logo-item';
                        logoItem.innerHTML = `
                            <img src="/cached-image/${logo.id}" alt="Logo ID: ${logo.id}" loading="lazy">
                            <div class="logo-details">
                                <p><strong>ID:</strong> ${logo.id}</p>
                                <p><strong>Original:</strong> ${logo.original_name}</p>
                                <input type="text" value="${logo.url}" readonly class="url-input">
                            </div>
                            <div class="actions">
                                <button class="action-btn copy-btn" data-url="${logo.url}">Copy Cloudinary Link</button>
                                <button class="action-btn delete delete-btn" data-id="${logo.id}" data-filename="${logo.original_name}">Delete</button>
                            </div>
                        `;
                        logoGallery.appendChild(logoItem);
                    });
                    attachEventListeners();
                } catch (error) {
                    console.error('Error fetching logos:', error);
                    logoGallery.innerHTML = '<p style="color: red;">Error loading logos.</p>';
                }
            }

            function attachEventListeners() {
                document.querySelectorAll('.copy-btn').forEach(button => {
                    button.onclick = async () => {
                        const urlToCopy = button.dataset.url;
                        let copiedSuccessfully = false;
                        if (navigator.clipboard && window.isSecureContext) {
                            try {
                                await navigator.clipboard.writeText(urlToCopy);
                                copiedSuccessfully = true;
                            } catch (err) {
                                console.error('Modern copy failed:', err);
                            }
                        }
                        if (!copiedSuccessfully) {
                            const textArea = document.createElement('textarea');
                            textArea.value = urlToCopy;
                            textArea.style.position = 'fixed';
                            textArea.style.top = '-9999px';
                            textArea.style.left = '-9999px';
                            document.body.appendChild(textArea);
                            textArea.focus();
                            textArea.select();
                            try {
                                copiedSuccessfully = document.execCommand('copy');
                            } catch (err) {
                                console.error('Fallback copy failed:', err);
                            }
                            document.body.removeChild(textArea);
                        }
                        if (copiedSuccessfully) {
                            button.textContent = 'Copied!';
                            setTimeout(() => { button.textContent = 'Copy Cloudinary Link'; }, 2000);
                        } else {
                            alert('Failed to copy. Please copy the link manually.');
                        }
                    };
                });

                document.querySelectorAll('.delete-btn').forEach(button => {
                    button.onclick = async () => {
                        const id = button.dataset.id;
                        const filename = button.dataset.filename;
                        if (confirm(`Are you sure you want to delete logo ID ${id} (${filename})?`)) {
                            showMessage(`Deleting logo ID ${id}...`, 'info');
                            try {
                                const response = await fetch(`/api/logos/${id}`, { method: 'DELETE' });
                                const data = await response.json();
                                if (response.ok) {
                                    showMessage(data.message, 'success');
                                    fetchLogos();
                                } else {
                                    showMessage(`Delete failed: ${data.error}`, 'error');
                                }
                            } catch (error) {
                                showMessage(`Delete failed: ${error}`, 'error');
                            }
                        }
                    };
                });
            }

            uploadForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                if (!fileInput.files.length) {
                    showMessage('Please select at least one file.', 'error');
                    return;
                }
                const formData = new FormData(uploadForm);
                showMessage(`Uploading ${fileInput.files.length} file(s)...`, 'info');
                try {
                    const response = await fetch('/upload', { method: 'POST', body: formData });
                    const data = await response.json();
                    if (response.ok) {
                        let msg = '';
                        if (Array.isArray(data)) {
                            const successCount = data.filter(r => r.message).length;
                            const errorCount = data.filter(r => r.error).length;
                            msg = `Uploaded ${successCount} file(s), ${errorCount} failed.`;
                        } else {
                            msg = data.message || `Success!`;
                        }
                        showMessage(msg, 'success');
                        fileInput.value = '';
                        fetchLogos();
                    } else {
                        throw new Error(data.error || 'Unknown upload error');
                    }
                } catch (error) {
                    showMessage(`Upload failed: ${error.message}`, 'error');
                }
            });

            document.addEventListener('DOMContentLoaded', fetchLogos);
        </script>
    </body>
    </html>
    """
    return render_template_string(template, version=__version__)

# --- Main entry point ---
if __name__ == '__main__':
    # Ensure data directories exist on startup
    os.makedirs(os.path.join('data', 'images'), exist_ok=True)
    os.makedirs(os.path.join('data', 'cache'), exist_ok=True)
    if not os.path.exists(DB_FILE):
        save_logos([])
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f: json.dump({}, f)
    app.run(debug=False, host='0.0.0.0', port=8084)