from flask import Flask, request, render_template, redirect, url_for, flash
from flask_uploads import UploadSet, configure_uploads, IMAGES
from urllib.parse import quote
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField
from wtforms.validators import DataRequired
import os
import re

# Create the Flask app instance
app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key'

# Define the upload sets
VIDEOS = UploadSet("videos", extensions=("mp4", "mov", "avi"))
IMAGES = UploadSet("images", extensions=("jpg", "jpeg", "png"))

# Configure the app with upload destinations
app.config["UPLOADED_VIDEOS_DEST"] = os.path.join("static", "uploads", "videos")
app.config["UPLOADED_IMAGES_DEST"] = os.path.join("static", "uploads", "images")

# Correctly configure Flask-Uploads with a list of upload sets
configure_uploads(app, [IMAGES, VIDEOS])  # Pass upload sets in a list

# Ensure upload directories exist
os.makedirs(app.config["UPLOADED_VIDEOS_DEST"], exist_ok=True)
os.makedirs(app.config["UPLOADED_IMAGES_DEST"], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in IMAGES.extensions

# Custom implementation to sanitize filenames (replacing secure_filename)
def sanitize_filename(filename):
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)  # Replace invalid characters
    return filename.strip("._")  # Remove leading/trailing dots or underscores

class UploadForm(FlaskForm):
    image_file = FileField('Image File', validators=[DataRequired()])
    file_path = StringField('File Path', validators=[DataRequired()])
    submit = SubmitField('Upload')

# Route for uploading files
@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    form = UploadForm()
    if form.validate_on_submit():
        if form.image_file.data:
            filename = sanitize_filename(form.image_file.data.filename)
            form.image_file.data.save(os.path.join(app.config['UPLOADED_IMAGES_DEST'], filename))
            flash('Image successfully uploaded', 'success')
            return redirect(url_for('index'))
    return render_template('upload.html', form=form)

@app.route('/upload_from_path', methods=['POST'])
def upload_from_path():
    form = UploadForm()
    file_path = request.form['file_path']
    if os.path.exists(file_path) and allowed_file(file_path):
        filename = sanitize_filename(os.path.basename(file_path))
        os.rename(file_path, os.path.join(app.config['UPLOADED_IMAGES_DEST'], filename))
        return redirect(url_for('index'))
    return render_template('upload.html', form=form)

# Route for the home page
@app.route('/')
def index():
    # Example posts data
    posts = [
        {"title": "Post 1", "description": "Description 1", "image_file": "image1.jpg"},
        {"title": "Post 2", "description": "Description 2", "video_file": "video1.mp4"}
    ]
    return render_template('index.html', posts=posts)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/latest-art', endpoint='latest_art')
def latest_art():
    return render_template('latest_art.html')
    
@app.route('/sold')
def sold():
    return render_template('sold.html')

@app.route('/commissions')
def commissions():
    return render_template('commissions.html')

if __name__ == "__main__":
    # Use 0.0.0.0 to make the server accessible externally
    app.run(debug=True, host="0.0.0.0", port=5000)