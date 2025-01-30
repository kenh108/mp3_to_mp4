import os
import uuid
from flask import Flask, request, render_template, redirect, url_for, jsonify

app = Flask(__name__)

UPLOAD_FOLDER='uploads'
ALLOWED_IMAGE_TYPES = {'png', 'jpg', 'jpeg'}
ALLOWED_AUDIO_TYPES = {'mp3'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 16mb limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/config')
def get_config():
    return jsonify({"max_file_size": app.config['MAX_CONTENT_LENGTH']})

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files or 'audio' not in request.files:
        return jsonify({"message": "both image and mp3 required"}), 400

    image = request.files['image']
    audio = request.files['audio']

    if image.filename == '' or audio.filename == '':
        return jsonify({"message": "both files not selected"}), 400

    if not allowed_file(image.filename, ALLOWED_IMAGE_TYPES):
        return jsonify({"message": "invalid image format; only png, jpg, jpeg accepted"}), 400

    if not allowed_file(audio.filename, ALLOWED_AUDIO_TYPES):
        return jsonify({"message": "invalid audio format; only mp3 accepted"}), 400

    unique_image_filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
    unique_audio_filename = str(uuid.uuid4()) + os.path.splitext(audio.filename)[1]

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_image_filename)
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_audio_filename)
    
    image.save(image_path)
    audio.save(audio_path)

    return jsonify({"message": f"files uploaded successfully: {image.filename}, {audio.filename}"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
