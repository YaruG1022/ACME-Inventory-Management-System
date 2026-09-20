import qrcode
from io import BytesIO
from base64 import b64encode
import imghdr
from werkzeug.utils import secure_filename
import werkzeug.exceptions
from flask import current_app
import os

# allowed image extensions
allowed_image_extensions = { 'png', 'jpg', 'jpeg', 'gif', 'webp', 'jfif'}


def get_qr_base64(data):
    qr = qrcode.QRCode(version=1, box_size=6, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    data_buffer = BytesIO()
    img.save(data_buffer)
    return b64encode(data_buffer.getvalue()).decode("utf-8")

def upload_image(image, folder, new_fname):

    ## Check file
    if image is None:
        return (False, "No image uploaded!")
    if folder is None:
        return (False, "No folder selected!")
    if image.filename == '':
        return (False, "Empty file name!")
    if '.' not in image.filename:
        return (False, "No file extension, invalid upload!")
    extension = image.filename.rsplit('.', 1)[1].lower()
    if(not extension in allowed_image_extensions):
        return (False, "Invalid file extension!")
    if validate_image(image) is False:
        return (False, "Invalid file!")
    
    # All checks passed
    
    final_filename = secure_filename(str(new_fname) + '.' + extension)
    upload_dir = os.path.join(current_app.config['IMG_URL'], folder)
    path = os.path.join(upload_dir + "/" + final_filename)

    try:
        image.save(path)
    except(werkzeug.exceptions.RequestEntityTooLarge):
        return (False, "File too large. Max file size is " + current_app.config['MAX_CONTENT_LENGTH'] / (1000000) + " MB")
    
    # file successfully uploaded
    return (True, path)
    

# Verify image is valid
def validate_image(data):
    header = data.read(512) # read header to check content type
    data.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return False # data isn't a valid image file
    return True # data is a valid image file


