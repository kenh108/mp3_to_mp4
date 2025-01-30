import os
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

UPLOAD_FOLDER='uploads'
ALLOWED_IMAGE_TYPES = {'png', 'jpg', 'jpeg'}
ALLOWED_AUDIO_TYPES = {'mp3'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files or 'audio' not in request.files:
        return "image and mp3 required", 400

    image = request.files['image']
    audio = request.files['audio']

    if image.filename == '' or audio.filename == '':
        return "image and mp3 required", 400

    if not allowed_file(image.filename, ALLOWED_IMAGE_TYPES):
        return "invalid image format", 400

    if not allowed_file(audio.filename, ALLOWED_AUDIO_TYPES):
        return "invalid audio format", 400

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio.filename)
    
    image.save(image_path)
    audio.save(audio_path)

    return f"files uploaded successfully: {image.filename}, {audio.filename}"

        
if __name__ == '__main__':
    app.run(debug=True, port=5000)
