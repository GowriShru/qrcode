from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename
import qrcode
from PIL import Image
import io
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_qr_code(data, color="black", background="white", logo_path=None):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color=color, back_color=background).convert('RGBA')

        if logo_path and os.path.exists(logo_path):
            logo = Image.open(logo_path).convert('RGBA')
            logo_size = (qr_img.size[0] // 4, qr_img.size[1] // 4)
            logo.thumbnail(logo_size)
            
            logo_pos = (
                (qr_img.size[0] - logo.size[0]) // 2,
                (qr_img.size[1] - logo.size[1]) // 2,
            )
            qr_img.paste(logo, logo_pos, logo)

        return qr_img
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None

def generate_upi_qr(upi_id, name, amount=None, currency="INR"):
    """Generate UPI payment QR code data"""
    if amount:
        return f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu={currency}"
    return f"upi://pay?pa={upi_id}&pn={name}&cu={currency}"

def generate_bitcoin_qr(address, amount=None):
    """Generate Bitcoin payment QR code data"""
    if amount:
        return f"bitcoin:{address}?amount={amount}"
    return f"bitcoin:{address}"

@app.route('/', methods=['GET', 'POST'])
def index():
    qr_code = None
    if request.method == 'POST':
        qr_type = request.form.get('qr_type', 'standard')
        
        if qr_type == 'standard':
            data = request.form.get('data')
            color = request.form.get('color', 'black')
            background = request.form.get('background', 'white')
            logo = request.files.get('logo')
            
            if not data:
                flash('Please provide data for the QR code', 'error')
                return redirect(url_for('index'))
                
            logo_path = None
            if logo and logo.filename != '':
                if allowed_file(logo.filename):
                    filename = secure_filename(logo.filename)
                    logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    logo.save(logo_path)
                else:
                    flash('Invalid file type for logo. Please use PNG, JPG, or JPEG.', 'error')
                    return redirect(url_for('index'))
            
            qr_img = generate_qr_code(data, color=color, background=background, logo_path=logo_path)
        
        elif qr_type == 'upi':
            upi_id = request.form.get('upi_id')
            name = request.form.get('upi_name')
            amount = request.form.get('upi_amount')
            color = request.form.get('color', 'black')
            background = request.form.get('background', 'white')
            logo = request.files.get('logo')
            
            if not upi_id or not name:
                flash('Please provide UPI ID and name', 'error')
                return redirect(url_for('index'))
                
            data = generate_upi_qr(upi_id, name, amount)
            
            logo_path = None
            if logo and logo.filename != '':
                if allowed_file(logo.filename):
                    filename = secure_filename(logo.filename)
                    logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    logo.save(logo_path)
                else:
                    flash('Invalid file type for logo. Please use PNG, JPG, or JPEG.', 'error')
                    return redirect(url_for('index'))
            
            qr_img = generate_qr_code(data, color=color, background=background, logo_path=logo_path)
        
        elif qr_type == 'bitcoin':
            address = request.form.get('bitcoin_address')
            amount = request.form.get('bitcoin_amount')
            color = request.form.get('color', 'black')
            background = request.form.get('background', 'white')
            logo = request.files.get('logo')
            
            if not address:
                flash('Please provide Bitcoin address', 'error')
                return redirect(url_for('index'))
                
            data = generate_bitcoin_qr(address, amount)
            
            logo_path = None
            if logo and logo.filename != '':
                if allowed_file(logo.filename):
                    filename = secure_filename(logo.filename)
                    logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    logo.save(logo_path)
                else:
                    flash('Invalid file type for logo. Please use PNG, JPG, or JPEG.', 'error')
                    return redirect(url_for('index'))
            
            qr_img = generate_qr_code(data, color=color, background=background, logo_path=logo_path)
        
        if qr_img is None:
            flash('Failed to generate QR code', 'error')
            return redirect(url_for('index'))
        
        # Convert image to base64 for displaying in HTML
        buffered = io.BytesIO()
        qr_img.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Save the image to a temporary file for download
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_qr.png')
        qr_img.save(temp_path)
        
        # Clean up logo file
        if logo_path and os.path.exists(logo_path):
            os.remove(logo_path)
    
    return render_template('index.html', qr_code=qr_code)

@app.route('/download')
def download():
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_qr.png')
    if os.path.exists(temp_path):
        return send_file(
            temp_path,
            mimetype='image/png',
            as_attachment=True,
            download_name='artistic_qr.png'
        )
    flash('No QR code available to download', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)