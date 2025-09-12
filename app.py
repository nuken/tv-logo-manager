# tv-logo-manager/app.py
from flask import Flask, request, send_from_directory, jsonify, redirect, send_file, Response
import os
from werkzeug.utils import secure_filename
import json
from PIL import Image, ImageOps
import io
import cloudinary
import cloudinary.uploader
import cloudinary.api
import sys

app = Flask(__name__)

# --- Configuration ---
UPLOAD_FOLDER = 'data/images'
DB_FILE = 'data/logos.json'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Cloudinary Configuration ---
# Read credentials from environment variables
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

# Exit if credentials are not set
if not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
    sys.exit("Error: CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET must be set as environment variables.")

cloudinary.config(
  cloud_name = CLOUDINARY_CLOUD_NAME,
  api_key = CLOUDINARY_API_KEY,
  api_secret = CLOUDINARY_API_SECRET
)

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

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handles new image uploads, processes them, and uploads to Cloudinary.
    """
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
            processed_img = process_logo_image(temp_filepath)
            
            # Save processed image to a buffer as PNG
            img_byte_arr = io.BytesIO()
            processed_img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(img_byte_arr, folder="tv-logos")
            os.remove(temp_filepath) # Remove temporary file

            logos = load_logos()
            
            # Generate a new unique ID
            new_id = max([l['id'] for l in logos]) + 1 if logos else 1
            logos.append({
                "id": new_id,
                "public_id": upload_result['public_id'],
                "original_name": original_filename,
                "url": upload_result['secure_url']
            })
            save_logos(logos)
            results.append({"message": "File uploaded and processed", "id": new_id, "url": upload_result['secure_url']})

        except Exception as e:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            app.logger.error(f"Image processing failed for {original_filename}: {e}")
            results.append({"error": f"Image processing failed for {original_filename}: {e}"})

    if len(results) == 1:
        return jsonify(results[0]), 200 if "message" in results[0] else 500
    else:
        status_code = 200 if any("message" in r for r in results) else 500
        return jsonify(results), status_code


@app.route('/images', methods=['GET'])
def get_image():
    """
    Redirects to the Cloudinary URL for the image.
    """
    image_id = request.args.get('id')
    if not image_id:
        return jsonify({"error": "Missing image ID"}), 400

    logos = load_logos()
    logo = next((l for l in logos if str(l['id']) == image_id), None)

    if logo and 'url' in logo:
        return redirect(logo['url'])
    
    return jsonify({"error": "Image not found"}), 404

@app.route('/api/logos', methods=['GET'])
def list_logos():
    """Returns a JSON list of all uploaded logo metadata with their direct Cloudinary URLs."""
    logos = load_logos()
    sorted_logos = sorted(logos, key=lambda x: x.get('id', 0))
    return jsonify(sorted_logos)

@app.route('/api/logos/<int:logo_id>', methods=['DELETE'])
def delete_logo(logo_id):
    """Deletes a logo by its ID from the local DB and Cloudinary."""
    logos = load_logos()
    logo_to_delete = next((logo for logo in logos if logo['id'] == logo_id), None)

    if not logo_to_delete:
        return jsonify({"error": f"Logo ID {logo_id} not found."}), 404
        
    try:
        # Delete from Cloudinary
        cloudinary.uploader.destroy(logo_to_delete['public_id'])
        
        # Remove from local DB
        logos_after_deletion = [logo for logo in logos if logo['id'] != logo_id]
        save_logos(logos_after_deletion)
        
        return jsonify({"message": f"Logo ID {logo_id} deleted successfully."}), 200
    except Exception as e:
        app.logger.error(f"Failed to delete logo ID {logo_id}: {e}")
        return jsonify({"error": f"Failed to delete logo ID {logo_id}: {e}"}), 500

@app.route('/')
def index():
    """Serves the main HTML page."""
    return """
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>TV Logo Manager</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f4f7f6; color: #333; }
            .container { max-width: 1000px; margin: 0 auto; background-color: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1); }
            h1, h2 { color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; margin-top: 30px; }
            #uploadForm { display: flex; flex-direction: column; gap: 15px; margin-bottom: 25px; padding: 20px; border: 1px dashed #bdc3c7; border-radius: 6px; background-color: #fcfcfc; }
            #fileInput { padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
            input[type="submit"] { background-color: #3498db; color: white; border: none; padding: 12px 20px; border-radius: 4px; cursor: pointer; font-size: 1rem; transition: background-color 0.2s ease; }
            input[type="submit"]:hover { background-color: #2980b9; }
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>TV Logo Manager</h1>
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
                            <img src="${logo.url}" alt="Logo ID: ${logo.id}" loading="lazy">
                            <div class="logo-details">
                                <p><strong>ID:</strong> ${logo.id}</p>
                                <p><strong>Original:</strong> ${logo.original_name}</p>
                                <input type="text" value="${logo.url}" readonly class="url-input">
                            </div>
                            <div class="actions">
                                <button class="action-btn copy-btn" data-url="${logo.url}">Copy Link</button>
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
                    button.onclick = () => {
                        const urlToCopy = button.dataset.url;
                        navigator.clipboard.writeText(urlToCopy).then(() => {
                            button.textContent = 'Copied!';
                            setTimeout(() => { button.textContent = 'Copy Link'; }, 2000);
                        }, () => {
                            alert('Failed to copy URL.');
                        });
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

# --- Main entry point for Flask app ---
if __name__ == '__main__':
    # Ensure data directories exist on startup
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump([], f)

    app.run(debug=False, host='0.0.0.0', port=8084)