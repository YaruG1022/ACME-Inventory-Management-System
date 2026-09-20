from flask import Flask, render_template, request, url_for, make_response, redirect, jsonify, flash, current_app, g
from markupsafe import escape

import secrets
from pathlib import Path

from datetime import datetime
from models import *
from flask_login import LoginManager
import os
from login_bp import login_bp, bcrypt
from interface import interface_bp
from sqlalchemy import func
import werkzeug.exceptions
from werkzeug.utils import secure_filename
from report_bp import report_bp
from inventory_bp import inventory_bp

import configparser


app = Flask(__name__) # create flask app
app.register_blueprint(login_bp) # register login blueprint
app.register_blueprint(interface_bp) # register login blueprint
app.register_blueprint(report_bp) # register report blueprint
app.register_blueprint(inventory_bp) # register inventory blueprint

config = configparser.ConfigParser()
config.read('server.ini')


###-------- Initialization --------###
basedir = os.path.abspath(os.path.dirname(__file__))

# Generate crucial directories
# Note: default_profile.png is important, do not delete
required_folders = [ "data/", "static/img", "static/img/items", "static/img/profiles"]

for dir in required_folders:
    if(os.path.isdir(dir) == False):
        os.makedirs(os.path.join(basedir, dir))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, "data/inventory.db")
# image upload base url
app.config['IMG_URL'] = "static/img/"
# max file size
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

# generate secret key if it doesn't exist
SECRET_FILE_PATH = Path("secret.txt")
try:
    # read secret key from file
    with SECRET_FILE_PATH.open("r") as secret_file:
        app.config['SECRET_KEY'] = secret_file.read()
except FileNotFoundError:
    # File not found, generate secret key file
    with SECRET_FILE_PATH.open("w") as secret_file:
        app.secret_key = secrets.token_urlsafe(32)
        secret_file.write(app.secret_key)

db.init_app(app)
bcrypt.init_app(app)

###-------- Startup --------###

## Login manager
login_manager = LoginManager()
login_manager.login_view = 'interface_bp.login_dialogue'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# database creation function
def create_db():
    with app.app_context():
        db.create_all()
# create database files if they do not exist
create_db()

###-------- Routes --------###

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/item_form")
def additem_test_form():
    return render_template("additem_form.html")

@app.route("/neworder", methods=['GET', 'POST'])
def neworder():
    order_page = url_for("interface_bp.add_order_pg")

    order_items = request.form['itemdata']
    order_date = datetime.datetime.strptime((request.form['order-date']), '%Y-%m-%d')
    recipient_address = request.form['recipient-address']
    recipient_name = request.form['recipient-name']

    # reduce item quantities

    entries = order_items.split(',') # split into comma separated values ("1x5", "15x3", etc)
    print("Entries: " + str(entries))
    items = []
    increment = 0
    for entry in entries:
        data = entry.split('x') # split entry ("1x5" to [1,5])
        print(data)
        itm_id = int(data[0])
        itm_quantity = int(data[1])
        item = Item.getItemByID(int(itm_id))
        oldquantity = item.quantity
        newquantity = oldquantity - itm_quantity
        if newquantity < 0:
            flash("Error: Invalid quantity for '" + item.name + "' (Available: " + str(oldquantity) + ")" )
            return redirect(order_page)
        else:
            item.quantity = newquantity

    Order.addOrder(order_date, None, "Confirmed", order_items, recipient_name, recipient_address)
    db.session.commit()

    flash("Order successful!")
    return redirect(order_page)

@app.route("/additem", methods=['GET', 'POST'])
def additem():
    donation_page = url_for("interface_bp.donation_pg")
    # id or name must be selected
    itm_id = escape(request.form['item-id'])
    itm_name = escape(request.form['item-name'])
    itm_quantity = escape(request.form['item-quantity'])
    itm_type = ""
    if('item-type' in request.form): 
        itm_type = escape(request.form['item-type'])
    else: itm_type = None
    stockdate = datetime.datetime.strptime(request.form['stock-date'], '%Y-%m-%d')
    expdate = datetime.datetime.strptime(request.form['expiry-date'], '%Y-%m-%d')
    
    VALID_ITEM_TYPES = { 'Food', 'Hygiene' }

    # if item id/name not set, quit
    if(not (itm_id or itm_name)):
        flash("Product not selected.")
        return redirect(donation_page)
    if(itm_type not in VALID_ITEM_TYPES and (itm_type is not None)):
        flash("Invalid product type.")
        return redirect(donation_page)
    # get image upload directory
    img_path = ""

    if request.files['item-image'].filename == '' or 'item-image' not in request.files:
        # no file uploaded, use default
        img_path = os.path.join(app.config['IMG_URL'], 'placeholder.png')
    else: 
        ## Get image filename
        if(itm_id == "" or itm_id is None):
            ## is column empty?
            if(len(Item.query.all()) != 0):
                img_name = db.session.query(func.max(Item.id)).scalar() + 1 # new item
            else:
                img_name = "1"
        else:
            img_name = itm_id # existing item
        
        upload_success = server_utils.upload_image(request.files['item-image'], "profiles", img_name)

        if(upload_success[0] == False):
            flash(upload_success[1])
            return redirect(donation_page)

        else:
            img_path = upload_success[1]

    ## New item
    if(itm_id == "" or itm_id is None):
        print(img_path)
        Item.addItem(itm_name, itm_quantity, stockdate, expdate, itm_type, img_path)
    # Updating item
    elif(itm_type is None):
        itm = Item.query.filter_by(id = itm_id).first()
        itm.quantity += int(itm_quantity)
        itm.stockdate = stockdate
        itm.expdate = expdate
        itm.image = img_path
        db.session.commit()
    #error
    else:
        flash("Select a valid item type if creating a new item.")
        return redirect(donation_page)
        
    resp = make_response(redirect(url_for("interface_bp.inventory_pg")))
    return resp

@app.route("/item_list")
def listitem_test():
    itemlist = Item.getAllItems()
    return render_template("itemlist_test.html", itemlist = itemlist)
    pass

@app.route("/success")
def success_page():
    return render_template("success.html")


@app.route("/search_item", methods=['GET'])
def search_item():
    query = request.args.get('search')
    print(query)
    if(query is None): item_list = Item.query.all()
    elif(query.isdigit()):
        item_list = Item.query.filter_by(id = int(query))
    else:
        item_list = Item.query.filter(Item.name.ilike("%" + query + "%"))
    result = ""
    
    if(item_list is None):
        return "No items found."
    #for itm in item_list:
    #    result += "(#" + str(itm.id) + "): " + itm.name + " x " + str(itm.quantity) + "<br>" 
    
    return jsonify([item.serialize() for item in item_list])
###-----------------------###

if __name__ == "__main__":
    if(config['SSL'].getboolean('SSL_Enabled') == True):
        # get certificates from server.ini
        ssl_cert_dir = config['SSL']['Server_Certificate']
        ssl_key_dir = config['SSL']['Server_Key']
        if(ssl_cert_dir is None or ssl_key_dir is None):
            print("NOTICE: No SSL key or certificate set, using dummy certificate.")
            app.run(ssl_context='adhoc') # use adhoc ssl certificate
        else:
            cert_folder = os.path.join(basedir, "certs/")
            ssl_cert_fulldirectory = os.path.join(cert_folder, ssl_cert_dir)
            ssl_key_fulldirectory = os.path.join(cert_folder, ssl_key_dir)
            # check that cert/key files exist 
            if(os.path.isfile(ssl_cert_fulldirectory) and os.path.isfile(ssl_key_fulldirectory)):
                print("NOTICE: Using ssl certificate " + ssl_cert_dir + " and key " + ssl_key_dir)


                context = (ssl_cert_fulldirectory, ssl_key_fulldirectory)
                app.run(host='0.0.0.0', port=5000, ssl_context=context)
            else:
                print("NOTICE: SSL certificate or key not found. Check that the files are in src/certs/ and named properly in server.ini")
                print("NOTICE: No SSL key or certificate set, using dummy certificate.")
                app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')
    else:
        # run without SSL
        print("NOTICE: Running without TLS encryption.")
        app.run(host='0.0.0.0', port=5000)