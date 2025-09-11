# tv-logo-manager/app.py
from flask import Flask, request, send_from_directory, jsonify, redirect, send_file, Response, session, url_for
import os
from werkzeug.utils import secure_filename
import json
from PIL import Image, ImageOps
import io
from imgurpython import ImgurClient

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration for image uploads and data storage
UPLOAD_FOLDER = 'data/images'
DB_FILE = 'data/logos.json'
IMGUR_CLIENT_ID = 'YOUR_CLIENT_ID'  # Replace with your Imgur client ID
IMGUR_CLIENT_SECRET = 'YOUR_CLIENT_SECRET'  # Replace with your Imgur client secret

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

imgur_client = ImgurClient(IMGUR_CLIENT_ID, IMGUR_CLIENT_SECRET)

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
def process_logo_image_to_webp(image_path):
    """
    Processes an image:
    1. Ensures it has an alpha channel (for transparency).
    2. Enforces a 4:3 aspect ratio using padding (letterboxing/pillarboxing).
    3. Resizes to a standard dimension (720x540 pixels).
    4. Returns the processed PIL Image object.
    """
    img = Image.open(image_path).convert("RGBA")

    target_width = 720
    target_height = 540
    target_size = (target_width, target_height)

    padded_img = ImageOps.pad(img, target_size, color=(0,0,0,0), centering=(0.5, 0.5))

    return padded_img

# --- Flask Routes ---

@app.route('/imgur_auth')
def imgur_auth():
    """Redirects the user to Imgur for authentication."""
    authorization_url = imgur_client.get_auth_url('code')
    return redirect(authorization_url)

@app.route('/imgur_callback')
def imgur_callback():
    """Handles the callback from Imgur after authentication."""
    code = request.args.get('code')
    credentials = imgur_client.authorize(code, 'authorization_code')
    imgur_client.set_user_auth(credentials['access_token'], credentials['refresh_token'])
    session['imgur_credentials'] = credentials
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handles new image uploads (single or multiple).
    The 'reupload' functionality is removed, this endpoint only adds new images.
    """
    if 'imgur_credentials' not in session:
        return jsonify({"error": "Please login to Imgur first"}), 401

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    uploaded_files = request.files.getlist('file')

    if not uploaded_files:
        return jsonify({"error": "No files selected"}), 400

    results = []
    for file in uploaded_files:
        if file.filename == '':
            results.append({"error": "Empty filename in multi-upload."})
            continue

        original_filename = secure_filename(file.filename)
        temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], "temp_" + original_filename)
        file.save(temp_filepath)

        try:
            # Upload to Imgur
            imgur_image = imgur_client.upload_from_path(temp_filepath, config=None, anon=False)
            os.remove(temp_filepath)  # Remove temporary file

            logos = load_logos()
            
            # Always generate a new unique ID for new uploads
            new_id = max([l['id'] for l in logos]) + 1 if logos else 1
            logos.append({"id": new_id, "filename": original_filename, "original_name": original_filename, "url": imgur_image['link'], "deletehash": imgur_image['deletehash']})
            save_logos(logos)
            results.append({"message": "File uploaded and processed", "id": new_id, "filename": original_filename, "url": imgur_image['link']})

        except Exception as e:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            app.logger.error(f"Image processing failed for {original_filename}: {e}")
            results.append({"error": f"Image processing failed for {original_filename}: {e}"})

    # Return appropriate response for single or multiple uploads
    if len(results) == 1: # If only one file uploaded, return single response
        if "error" in results[0]:
            return jsonify(results[0]), 500
        return jsonify(results[0]), 200
    else: # Multi-upload case
        all_errors = all("error" in r for r in results)
        status_code = 500 if all_errors else 200
        return jsonify(results), status_code


@app.route('/images', methods=['GET'])
def get_image():
    """
    Redirects to the Imgur URL for the image.
    """
    image_id = request.args.get('id')
    if not image_id:
        return jsonify({"error": "Missing image ID"}), 400

    logos = load_logos()
    logo = next((l for l in logos if str(l['id']) == image_id), None)

    if logo and 'url' in logo:
        return redirect(logo['url'])
    
    return jsonify({"error": "Image not found or no Imgur URL"}), 404

@app.route('/api/logos', methods=['GET'])
def list_logos():
    """Returns a JSON list of all uploaded logo metadata with their direct URLs."""
    logos = load_logos()
    logo_list = []
    # Sort logos by ID for consistent display order
    sorted_logos = sorted(logos, key=lambda x: x.get('id', 0)) # Use .get with default for robustness
    for logo in sorted_logos:
        logo_list.append({
            "id": logo['id'],
            "filename": logo['filename'],
            "original_name": logo['original_name'],
            "url": logo.get('url', '')
        })
    return jsonify(logo_list)

@app.route('/api/logos/<int:logo_id>', methods=['DELETE'])
def delete_logo(logo_id):
    """Deletes a logo by its ID."""
    if 'imgur_credentials' not in session:
        return jsonify({"error": "Please login to Imgur first"}), 401
    
    logos = load_logos()
    initial_len = len(logos)
    
    # Filter out the logo to be deleted
    logos_after_deletion = [logo for logo in logos if logo['id'] != logo_id]

    if len(logos_after_deletion) < initial_len:
        # Find the filename of the deleted logo to remove its file
        deleted_logo = next((logo for logo in logos if logo['id'] == logo_id), None)
        if deleted_logo:
            # Delete from Imgur
            if 'deletehash' in deleted_logo:
                try:
                    imgur_client.delete_image(deleted_logo['deletehash'])
                except Exception as e:
                    app.logger.error(f"Failed to delete image from Imgur: {e}")

            filepath = os.path.join(app.config['UPLOAD_FOLDER'], deleted_logo['filename'])
            if os.path.exists(filepath):
                os.remove(filepath)
                app.logger.info(f"Deleted file: {filepath}")
            else:
                app.logger.warning(f"File not found for deletion: {filepath}")
        
        save_logos(logos_after_deletion)
        return jsonify({"message": f"Logo ID {logo_id} deleted successfully."}), 200
    
    return jsonify({"error": f"Logo ID {logo_id} not found."}), 404

@app.route('/download/<int:logo_id>/<string:file_format>', methods=['GET'])
def download_image(logo_id, file_format):
    """
    Allows downloading an image by its ID in specified format (webp or png).
    """
    logos = load_logos()
    logo = next((l for l in logos if str(l['id']) == str(logo_id)), None)

    if not logo:
        return jsonify({"error": "Logo not found"}), 404

    current_filename = logo['filename']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], current_filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "Image file not found on server"}), 404

    # Ensure the requested format is valid
    if file_format not in ['webp', 'png']:
        return jsonify({"error": "Invalid file format requested. Must be 'webp' or 'png'."}), 400

    download_name_base = os.path.splitext(logo['original_name'])[0] # Use original name as base

    if file_format == 'webp':
        mimetype = 'image/webp'
        download_filename = f"{download_name_base}.webp"
        return send_file(filepath, mimetype=mimetype, as_attachment=True, download_name=download_filename)
    
    elif file_format == 'png':
        mimetype = 'image/png'
        download_filename = f"{download_name_base}.png"
        
        try:
            # Open the existing WebP image
            img = Image.open(filepath)
            
            # Convert to RGBA (for transparency) and save as PNG to a BytesIO object
            img_byte_arr = io.BytesIO()
            img.convert("RGBA").save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0) # Rewind to the beginning of the buffer
            
            return send_file(img_byte_arr, mimetype=mimetype, as_attachment=True, download_name=download_filename)
        except Exception as e:
            app.logger.error(f"Error converting and serving PNG for logo ID {logo_id}: {e}")
            return jsonify({"error": f"Failed to convert and download image as PNG: {e}"}), 500

@app.route('/')
def index():
    """Serves the main HTML page with upload form and logo gallery."""
    return """
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>TV Logo Manager</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 20px;
                background-color: #f4f7f6;
                color: #333;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background-color: #fff;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            }
            h1, h2 {
                color: #2c3e50;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 10px;
                margin-top: 30px;
            }
            #uploadForm {
                display: flex;
                flex-direction: column;
                gap: 15px;
                margin-bottom: 25px;
                padding: 20px;
                border: 1px dashed #bdc3c7;
                border-radius: 6px;
                background-color: #fcfcfc;
            }
            #fileInput {
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            input[type="submit"], .auth-btn {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 1rem;
                transition: background-color 0.2s ease;
                text-decoration: none;
                text-align: center;
            }
            input[type="submit"]:hover, .auth-btn:hover {
                background-color: #2980b9;
            }
            #uploadMessage {
                margin-top: 15px;
                padding: 10px;
                border-radius: 4px;
                display: none;
            }
            #uploadMessage.info { background-color: #e9ecef; color: #333; }
            #uploadMessage.success { background-color: #d4edda; color: #155724; }
            #uploadMessage.error { background-color: #f8d7da; color: #721c24; }

            #logoGallery {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
                gap: 20px;
                padding: 10px 0;
            }
            .logo-item {
                border: 1px solid #e0e0e0;
                padding: 15px;
                background-color: #f3f3f3; /* Subtle grey for contrast */
                border-radius: 6px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
                min-width: 0;
            }
            .logo-item img {
                max-width: 100%;
                height: auto;
                max-height: 150px;
                border: 1px solid #eee;
                border-radius: 4px;
                object-fit: contain;
                margin-bottom: 10px;
                box-shadow: 0 0 8px rgba(0, 0, 0, 0.1);
            }
            .logo-details {
                width: 100%;
                flex-grow: 1;
            }
            .logo-details p {
                margin: 5px 0;
                font-size: 0.9rem;
                word-wrap: break-word;
            }
            .logo-details strong {
                color: #555;
            }
            .url-input {
                width: calc(100% - 16px);
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 0.8rem;
                background-color: #f7f7f7;
                cursor: text;
                overflow-x: auto;
            }
            .actions {
                margin-top: 10px;
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                justify-content: center;
                margin-top: auto;
            }
            .action-btn {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 12px;
                cursor: pointer;
                border-radius: 4px;
                font-size: 0.85rem;
                transition: background-color 0.2s ease;
                flex-grow: 1;
                min-width: 0;
            }
            .action-btn.delete { background-color: #dc3545; }
            .action-btn.download-png { background-color: #6c757d; }
            .action-btn.download-webp { background-color: #17a2b8; }


            .action-btn:hover { filter: brightness(1.1); }
            .action-btn:active { filter: brightness(0.9); }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>TV Logo Manager</h1>

            <a href="/imgur_auth" class="auth-btn">Login with Imgur</a>

            <h2>Upload New Logo(s)</h2>
            <form id="uploadForm" enctype="multipart/form-data">
              <input type="file" name="file" id="fileInput" accept="image/*" multiple required>
              <input type="submit" value="Upload Logo(s)">
            </form>
            <div id="uploadMessage"></div>

            <h2>Uploaded Logos</h2>
            <div id="logoGallery">
                <p>Loading logos...</p>
            </div>
        </div>

        <script>
            const uploadForm = document.getElementById('uploadForm');
            const fileInput = document.getElementById('fileInput');
            const uploadMessage = document.getElementById('uploadMessage');
            const logoGallery = document.getElementById('logoGallery');

            function showMessage(msg, type = 'info') {
                uploadMessage.textContent = msg;
                uploadMessage.className = ``;
                uploadMessage.classList.add(type);
                uploadMessage.style.display = 'block';
                setTimeout(() => { uploadMessage.style.display = 'none'; }, 5000);
            }

            async function fetchLogos() {
                try {
                    logoGallery.innerHTML = '<p>Loading logos...</p>';
                    const response = await fetch('/api/logos');
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const logos = await response.json();
                    logoGallery.innerHTML = '';

                    if (logos.length === 0) {
                        logoGallery.innerHTML = '<p>No logos uploaded yet. Upload one or more using the form above!</p>';
                        return;
                    }

                    logos.forEach(logo => {
                        const displayUrl = logo.url;

                        const logoItem = document.createElement('div');
                        logoItem.className = 'logo-item';
                        logoItem.innerHTML = `
                            <img src="${displayUrl}" alt="Logo ID: ${logo.id}" loading="lazy">
                            <div class="logo-details">
                                <p><strong>ID:</strong> ${logo.id}</p>
                                <p><strong>Original Name:</strong> ${logo.original_name}</p>
                                <p><strong>Imgur URL:</strong> <input type="text" value="${displayUrl}" readonly class="url-input"></p>
                            </div>
                            <div class="actions">
                                <button class="action-btn copy-btn" data-url="${displayUrl}">Copy Link</button>
                                <button class="action-btn delete delete-btn" data-id="${logo.id}" data-filename="${logo.original_name}">Delete</button>
                            </div>
                        `;
                        logoGallery.appendChild(logoItem);
                    });

                    attachEventListeners();
                } catch (error) {
                    console.error('Error fetching logos:', error);
                    logoGallery.innerHTML = '<p style="color: red;">Error loading logos. Please check server logs.</p>';
                }
            }

            function attachEventListeners() {
                document.querySelectorAll('.copy-btn').forEach(button => {
                    button.onclick = async () => {
                        const urlToCopy = button.dataset.url;
                        let copiedSuccessfully = false;

                        if (navigator.clipboard && navigator.clipboard.writeText) {
                            try {
                                await navigator.clipboard.writeText(urlToCopy);
                                copiedSuccessfully = true;
                                console.log('Copied using modern Clipboard API:', urlToCopy);
                            } catch (err) {
                                console.error('Failed to copy using modern Clipboard API:', err);
                            }
                        }

                        if (!copiedSuccessfully) {
                            const inputElement = button.parentElement.querySelector('.url-input');
                            let tempTextArea = null;

                            const elementToSelect = inputElement || (tempTextArea = document.createElement('textarea'));
                            if (tempTextArea) {
                                tempTextArea.value = urlToCopy;
                                tempTextArea.style.position = 'fixed';
                                tempTextArea.style.top = '0';
                                tempTextArea.style.left = '0';
                                tempTextArea.style.opacity = '0';
                                document.body.appendChild(tempTextArea);
                            }

                            try {
                                elementToSelect.select();
                                elementToSelect.setSelectionRange(0, 99999);
                                copiedSuccessfully = document.execCommand('copy');
                                console.log('Copied using document.execCommand:', copiedSuccessfully);
                            } catch (execErr) {
                                console.error('Failed to copy using document.execCommand:', execErr);
                            } finally {
                                if (tempTextArea) {
                                    document.body.removeChild(tempTextArea);
                                }
                            }
                        }

                        if (copiedSuccessfully) {
                            button.textContent = 'Copied!';
                            setTimeout(() => { button.textContent = 'Copy Link'; }, 2000);
                        } else {
                            alert('Failed to copy URL automatically. Please manually select and copy: ' + urlToCopy);
                            button.textContent = 'Copy Failed!';
                            setTimeout(() => { button.textContent = 'Copy Link'; }, 2000);
                        }
                    };
                });

                document.querySelectorAll('.delete-btn').forEach(button => {
                    button.onclick = async () => {
                        const id = button.dataset.id;
                        const filename = button.dataset.filename;
                        if (confirm(`Are you sure you want to delete logo ID ${id} (${filename})? This cannot be undone.`)) {
                            showMessage(`Deleting logo ID ${id}...`, 'info');
                            try {
                                const response = await fetch(`/api/logos/${id}`, {
                                    method: 'DELETE'
                                });
                                const data = await response.json();

                                if (response.ok) {
                                    showMessage(`Deleted logo ID ${id}.`, 'success');
                                    fetchLogos();
                                } else {
                                    showMessage(`Delete failed for ID ${id}: ${data.error || 'Unknown error'}`, 'error');
                                }
                            } catch (error) {
                                console.error('Delete failed:', error);
                                showMessage(`Delete failed for ID ${id}: ${error.message}.`, 'error');
                            }
                        }
                    };
                });
            }

            uploadForm.addEventListener('submit', async (event) => {
                event.preventDefault();

                if (!fileInput.files || fileInput.files.length === 0) {
                    showMessage('Please select at least one file to upload.', 'error');
                    return;
                }

                const formData = new FormData();
                for (let i = 0; i < fileInput.files.length; i++) {
                    formData.append('file', fileInput.files[i]);
                }

                showMessage(`Uploading ${fileInput.files.length} file(s)...`, 'info');
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();

                    if (response.ok) {
                        if (Array.isArray(data)) {
                            const successCount = data.filter(r => r.message).length;
                            const errorCount = data.filter(r => r.error).length;
                            showMessage(`Uploaded ${successCount} file(s), ${errorCount} failed.`, 'success');
                        } else {
                            showMessage(`Success: ${data.message} (ID: ${data.id})`, 'success');
                        }
                        fileInput.value = '';
                        fetchLogos();
                    } else {
                        let errorMsg = 'Unknown error during upload.';
                        if (data && data.error) {
                            errorMsg = data.error;
                        } else if (Array.isArray(data)) {
                            errorMsg = data.map(r => r.error || r.message).join('; ');
                        }
                        showMessage(`Upload failed: ${errorMsg}`, 'error');
                    }
                } catch (error) {
                    console.error('Upload failed:', error);
                    showMessage(`Upload failed: ${error.message}. Check console for details.`, 'error');
                }
            });

            document.addEventListener('DOMContentLoaded', fetchLogos);
        </script>
    </body>
    </html>
    """

# --- Main entry point for Flask app ---
if __name__ == '__main__':
    # Ensure data directories exist on startup
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    # Check if logos.json exists, if not, create an empty list
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump([], f)

    # Run the Flask app
    app.run(debug=False, host='0.0.0.0', port=8084)