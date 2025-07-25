from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory
from flask_uploads import UploadSet, configure_uploads, IMAGES
from urllib.parse import quote
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField
from wtforms.validators import DataRequired
import os
import re
from flask import jsonify
from flask import session
import requests
import paypalrestsdk
import json
# Create the Flask app instance
app = Flask(__name__, static_folder='static')
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

# Path to the testimonials JSON file
TESTIMONIALS_FILE = 'testimonials.json'

@app.route('/submit-testimonial', methods=['POST'])
def submit_testimonial():
    data = request.json
    testimonial_text = data.get('text')
    author_name = data.get('author')

    # Validate the input
    if not testimonial_text or not author_name:
        return jsonify({"success": False, "message": "Invalid input"}), 400

    # Load existing testimonials
    if os.path.exists(TESTIMONIALS_FILE):
        with open(TESTIMONIALS_FILE, 'r') as file:
            testimonials = json.load(file)
    else:
        testimonials = []

    # Append the new testimonial
    testimonials.append({"text": testimonial_text, "author": author_name})

    # Save the updated testimonials back to the file
    with open(TESTIMONIALS_FILE, 'w') as file:
        json.dump(testimonials, file)

    return jsonify({"success": True})

@app.route('/testimonials.json')
def get_testimonials():
    return send_from_directory('.', TESTIMONIALS_FILE)


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

@app.route('/potraits', endpoint='potrait')
def potrait():
    return render_template('potrait.html')
    
@app.route('/wildlife')
def wildlife():
    return render_template('wildlife.html')

@app.route('/contemporary')
def contemporary():
    return render_template('contemporary.html')


@app.route('/update_cart', methods=['POST'])
def update_cart():
    cart_data = request.json  # Get the cart data from the request
    session['cart'] = cart_data  # Store the cart in the session
    return {'status': 'success'}, 200  # Return a success response

# Add this route to handle PayPal payment creation
@app.route('/create_paypal_payment', methods=['POST'])
def create_paypal_payment():
    # PayPal API credentials
    client_id = 'AW8N4SbwM14-oYi6wkAv5PUX8Xwtt5eBGBizrtQSkJFMjQ4VcuY4gD55led846S5OfoB6hxOTnkuXVsa'
    secret = 'EB8ACPTTFfSzthmI2Kl1JRGxke4CVWjf8reVVaB7Ld20X-RkJatt2uhd51dbdje5VbhcRTZPEqMZVpL4'
    url = 'https://api.sandbox.paypal.com/v1/payments/payment'  # Use sandbox for testing

    # Get the order details from the request
    data = request.json
    total_amount = data['total']  # Total amount from the cart

    # Create the payment payload
    payload = {
        "intent": "sale",
        "redirect_urls": {
            "return_url": "http://localhost:5000/payment_success",  # Change to your success URL
            "cancel_url": "http://localhost:5000/"
        },
        "payer": {
            "payment_method": "paypal"
        },
        "transactions": [{
            "amount": {
                "total": str(total_amount),
                "currency": "USD"
            },
            "description": "Payment for your order"
        }]
    }

    # Make the request to PayPal
    response = requests.post(url, json=payload, auth=(client_id, secret))
    return jsonify(response.json())

# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": "live",  # or "live" for production
    "client_id": "AW8N4SbwM14-oYi6wkAv5PUX8Xwtt5eBGBizrtQSkJFMjQ4VcuY4gD55led846S5OfoB6hxOTnkuXVsa",
    "client_secret": "EB8ACPTTFfSzthmI2Kl1JRGxke4CVWjf8reVVaB7Ld20X-RkJatt2uhd51dbdje5VbhcRTZPEqMZVpL4"
})

@app.route('/capture_payment', methods=['POST'])
def capture_payment():
    # Get the order ID from the request
    order_id = request.json.get('orderID')

    # Capture the payment
    try:
        # Create a payment object
        payment = paypalrestsdk.Payment.find(order_id)

        # Check if the payment is approved
        if payment and payment.state == "approved":
            # Capture the payment
            capture = payment.capture({"amount": {"currency": "USD", "total": payment.transactions[0].amount.total}})

            if capture.success():
                return jsonify({'status': 'success', 'message': 'Payment captured successfully!'})
            else:
                return jsonify({'status': 'error', 'message': capture.error}), 400
        else:
            return jsonify({'status': 'error', 'message': 'Payment not approved or not found.'}), 400

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/payment')
def payment():
    cart_items = session.get('cart', [])  # Retrieve cart from session

    # Calculate total price
    total_price = sum(item['price'] for item in cart_items)  # Sum prices

    return render_template('payment.html', total_price=total_price, cart=cart_items)



# Ensure static files are served correctly
@app.route('/static/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)

if __name__ == "__main__":
    # Use 0.0.0.0 to make the server accessible externally
    app.run(debug=True, host="0.0.0.0", port=5000)