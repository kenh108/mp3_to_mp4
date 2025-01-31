import os
import uuid
import subprocess
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory, send_file
from PIL import Image
from mutagen.mp3 import MP3
from urllib.parse import quote, unquote

app = Flask(__name__)

UPLOAD_FOLDER='uploads'
OUTPUT_FOLDER='processed'
ALLOWED_IMAGE_TYPES = {'png', 'jpg', 'jpeg', 'webp'}
ALLOWED_AUDIO_TYPES = {'mp3'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER 
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 16mb limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Ensure file types are supported
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Ensure height and width are divisible by 2 for ffmpeg
def ensure_even_dimensions(image_path):
    img = Image.open(image_path)
    width, height = img.size

    if width % 2 == 0 and height % 2 == 0:
        return image_path

    new_width = width - (width % 2)
    new_height = height - (height % 2)

    img = img.resize((new_width, new_height), Image.LANCZOS)
    new_image_path = image_path.replace(".", "_even.")
    
    img.save(new_image_path)

    return new_image_path

def get_audio_duration(audio_path):
    audio = MP3(audio_path)
    return audio.info.length

@app.route('/config')
def get_config():
    return jsonify({"max_file_size": app.config['MAX_CONTENT_LENGTH']})

@app.route('/')
def upload_form():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'image' not in request.files or 'audio' not in request.files:
        return jsonify({"message": "both image and mp3 required"}), 400

    image = request.files['image']
    audio = request.files['audio']

    if image.filename == '' or audio.filename == '':
        return jsonify({"message": "both files not selected"}), 400

    if not allowed_file(image.filename, ALLOWED_IMAGE_TYPES):
        return jsonify({"message": "invalid image format; only png, jpg, jpeg, webp accepted"}), 400

    if not allowed_file(audio.filename, ALLOWED_AUDIO_TYPES):
        return jsonify({"message": "invalid audio format; only mp3 accepted"}), 400

    original_filename = audio.filename.rpartition(".")[0]
    original_filename_encoded = quote(original_filename)

    unique_image_filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
    unique_audio_filename = str(uuid.uuid4()) + os.path.splitext(audio.filename)[1]
    unique_processed_image_filename = str(uuid.uuid4()) + ".png"
    unique_processed_video_filename = str(uuid.uuid4()) + ".mp4"

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_image_filename)
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_audio_filename)
    processed_image_path = os.path.join(app.config['OUTPUT_FOLDER'], unique_processed_image_filename)
    processed_video_path = os.path.join(app.config['OUTPUT_FOLDER'], unique_processed_video_filename)
    
    image.save(image_path)
    audio.save(audio_path)

    ffmpeg_image_command = [
        "ffmpeg", "-y", "-i", image_path, "-filter_complex",
        "[0:v] scale=1920:1080:force_original_aspect_ratio=decrease [fg]; "
        "[0:v] scale=1920:1080:force_original_aspect_ratio=increase, crop=1920:1080, gblur=sigma=20 [bg]; "
        "[bg][fg] overlay=(W-w)/2:(H-h)/2",
        "-compression_level", "0", "-pred", "mixed", "-q:v", "1",
        processed_image_path
    ]

    try:
        subprocess.run(ffmpeg_image_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        return jsonify({"message": f"ffmpeg error processing image: {e.stderr.decode()}"}), 500

    audio_duration = get_audio_duration(audio_path)

    ffmpeg_video_command = [
        "ffmpeg", "-y", "-loop", "1",
        "-i", processed_image_path,
        "-i", audio_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-tune", "stillimage", "-c:a", "copy",
        "-t", str(audio_duration),
        processed_video_path
    ]

    try:
        subprocess.run(ffmpeg_video_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        return jsonify({"message": f"ffmpeg error processing video: {e.stderr.decode()}"}), 500

    return jsonify({
        "message": "file processed successfully",
        "video_url": f"/download/{unique_processed_video_filename}?original={original_filename_encoded}"
    })

@app.route('/download/<filename>')
def download_video(filename):
    original_filename_encoded = request.args.get("original", "video") # default to "video" if original name is missing
    original_filename = unquote(original_filename_encoded)
    processed_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    print(original_filename)
    
    if not os.path.exists(processed_path):
        return jsonify({"message": "file not found"}), 404

    return send_file(processed_path, as_attachment=True, download_name=f"{original_filename}.mp4")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
