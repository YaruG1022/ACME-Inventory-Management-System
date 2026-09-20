
from flask import Flask, render_template, url_for, request, Blueprint
from flask_login import login_user, login_required, logout_user, current_user
from models import db, User, Item, Order
import datetime
interface_bp = Blueprint("interface_bp", __name__)

@interface_bp.route('/')
@interface_bp.route('/home')
def home_page():
    #Order.addOrder(datetime.datetime.now(), datetime.datetime.now(), "Shipped", "1x3,4x6,2x82,3x4", "Test recipient", "1234 Street Rd.")

    return render_template("homepage.html", title="Home")

@interface_bp.route('/add_donation')
@login_required
def donation_pg():
    return render_template("donation.html", title="Add Donation")

@interface_bp.route('/add_order')
@login_required
def add_order_pg():
    return render_template("add_order.html", title="Add Order")

@interface_bp.route('/inventory')
@login_required
def inventory_pg():
    # get items from inventory
    item_list = Item.getAllItems()

    return render_template("inventory.html", title="Inventory", items = item_list)

# @interface_bp.route('/inventory')
# @login_required
# def inventory_pg():
#     return render_template("inventory.html", title="Inventory")

@interface_bp.route('/report')
@login_required
def report_pg():
    return render_template("report.html", title="Report")

@interface_bp.route('/orders')
@login_required
def orders_pg():
    orders_list = Order.getAllOrders()
    itemlists = {}
    if(orders_list):
        for order in orders_list: # populate dictionary
            itemlists[order.id] = order.getOrderItems(order.id)
    else:
        orders_list = {}
    return render_template("orders.html", title="Orders", orders = orders_list, itemlists = itemlists)

@interface_bp.route('/account')
@login_required
def account_pg():
    return render_template("user_account.html", title="Account")

@interface_bp.route('/login_required')
def login_dialogue():
    return render_template("login_required.html", title="Login Required")