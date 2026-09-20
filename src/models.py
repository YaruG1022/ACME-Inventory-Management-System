from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import datetime
from flask import current_app
from flask_bcrypt import Bcrypt
import pyotp
import os
import server_utils

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # automatically increments
    email = db.Column(db.String(255), unique=True, nullable=False) # duplicate emails not allowed
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    pfp_url = db.Column(db.String(255))
    joindate = db.Column(db.DateTime, nullable=False)
    is_2fa_enabled = db.Column(db.Boolean, nullable = False, default = False)
    token_2fa = db.Column(db.String, unique=True)

    def __init__(self, email, name, password):
        default_pfp_dir = os.path.join(current_app.config['IMG_URL'], "profiles/default_profile.png")

        self.email = email
        self.name = name
        self.password = bcrypt.generate_password_hash(password)
        self.joindate = datetime.datetime.now()
        self.token_2fa = pyotp.random_base32()
        self.pfp_url = default_pfp_dir
        

    def __repr__(self):
        return '<Email: %r>' % self.email
    
    def get_2fa_url(self):
        return pyotp.totp.TOTP(self.token_2fa).provisioning_uri(name = self.email, issuer_name=current_app.name)
    
    def verify_otp(self, user_otp):
        totp = pyotp.parse_uri(self.get_2fa_url())
        return totp.verify(user_otp)
    
    def get_2fa_qr_b64(self):
        return server_utils.get_qr_base64(self.get_2fa_url())

## Item model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True) # item ids, automatically increments
    name = db.Column(db.String(255), nullable = False)
    type = db.Column(db.String(255), nullable = False) # food, hygiene
    quantity = db.Column(db.Integer, nullable = False)
    stockdate = db.Column(db.Date, nullable = False) # item last stock/restock date
    expdate = db.Column(db.Date, nullable = False) # item expiration date
    image = db.Column(db.String(255), nullable = True) # path to picture of item (optional)

    ## Item model functions
    def __repr__(self):
        return '<ID: %r>' % self.id
    
    def serialize(self):
        return { 
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'quantity': self.quantity,
            'stockdate': self.stockdate,
            'expdate': self.expdate,
            'image': self.image
        }
    
    def addItem(item_name, item_quantity, item_stockdate, item_expdate, item_type, item_img = None):
        new_item = Item(name = item_name, quantity = item_quantity, stockdate = item_stockdate, expdate = item_expdate, type = item_type, image = item_img)
        db.session.add(new_item)

        db.session.commit()

    def updateItem(item_id, item_name = None, item_quantity = None, item_stockdate = None, item_expdate = None, item_type = None, item_img = None):
        foundItem = Item.query.filter_by(id = item_id).first()
        if(item_name): foundItem.name = item_name
        if(item_quantity): foundItem.quantity = item_quantity
        if(item_stockdate): foundItem.stockdate = item_stockdate
        if(item_expdate): foundItem.expdate = item_expdate
        if(item_type): foundItem.type = item_type
        if(item_img): foundItem.image = item_img
        db.session.commit()


    def getAllItems():
        return Item.query.all()

    def getItemByID(item_id):
        return Item.query.filter_by(id = item_id).first()
    
    def deleteItemByID(item_id):
        itm = Item.query.filter_by(id = item_id).first()
        if(itm is None):
            print("Item  " + str(item_id) + " Not found!")
            return False
        else:
            db.session.delete(itm)
            db.session.commit()
            print("deleted item with ID: " + str(item_id) + "!")
            return True

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True) # order id, automatically increments
    orderdate = db.Column(db.Date, nullable = False)
    deliverydate = db.Column(db.Date, nullable = True) # can be empty until delivery
    status = db.Column(db.String(255), nullable = False)
    items = db.Column(db.String(255), nullable = False) # stored as comma separated item IDs with quantities in every element
                                                        # e.g.: "35x20, 60x14, 59x18"
    recipient_name = db.Column(db.String(255), nullable = False)
    recipient_address = db.Column(db.String(255), nullable = False)

    def serialize(self):
        return { 
            'id': self.id,
            'orderdate': self.orderdate,
            'deliverydate': self.deliverydate,
            'status': self.status,
            'items': self.items,
            'recipient_name': self.recipient_name,
            'recipient_address': self.recipient_address
        }
    
    def getAllOrders():
        return Order.query.all()

    def addOrder(o_orderdate, o_deliverydate, o_status, o_items, o_recipient_name, o_recipient_address):
        new_order = Order(orderdate = o_orderdate, deliverydate = o_deliverydate, status = o_status, items = o_items, recipient_name = o_recipient_name, recipient_address = o_recipient_address)
        db.session.add(new_order)
        db.session.commit()

    def getOrderByID(self, order_id):
        return self.query.filter_by(id = order_id).first()

    def changeStatus(self, order_id, new_status):
        order = self.getOrderByID(order_id)

        if(order is None):
            print("Order  " + str(order_id) + " Not found!")
            return False
        else:
            order.status = new_status
            db.session.commit()
            return True
    
    def deleteOrderByID(self, order_id):
        order = self.getOrderByID(order_id)
        if(order is None):
            print("Order  " + str(order_id) + " Not found!")
            return False
        else:
            order.delete()
            db.session.commit()
            return True
    
    # get item info from the IDs stored in the order items field
    def getOrderItems(self, order_id):
        order = self.getOrderByID(order_id)
        if(order is None):
            print("Order  " + str(order_id) + " Not found!")
            return None
        else:
            return itemstring_toitems(order.items) # return list of items


def itemstring_toitems(data):
    entries = data.split(',') # split into comma separated values ("1x5", "15x3", etc)
    print("Entries: " + str(entries))
    items = []
    increment = 0
    for entry in entries:
        data = entry.split('x') # split entry ("1x5" to [1,5])
        print(data)
        itm_id = int(data[0])
        itm_quantity = int(data[1])
        item = Item.getItemByID(int(itm_id))
        if(item):
            items.append((item.name, itm_quantity)) # add to dictionary

    print(items)
    return items # return list of items