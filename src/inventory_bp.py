from flask import Blueprint, request, render_template, jsonify, Blueprint, make_response, current_app
import sqlite3
from models import db, Item, User
import os
from datetime import datetime

inventory_bp = Blueprint('inventory_bp', __name__, template_folder='templates')

# Route to get inventory data
# @inventory_bp.route('/getInventoryData', methods=['GET'])
# def get_inventory_data():
#     conn = get_db_connection()
#     cursor = conn.execute('SELECT * FROM inventory')
#     rows = cursor.fetchall()
#     conn.close()
    
#     # Convert rows to a list of dictionaries
#     data = [dict(row) for row in rows]
#     columns = ['id', 'name', 'quantity', 'category', 'date_added', 'usable_until', 'status']
    
#     return jsonify({'columns': columns, 'data': data})

@inventory_bp.route('/getInventoryData', methods=['GET'])
def get_inventory_data():
    rows = Item.query.all()

    return jsonify([item.serialize() for item in rows])

# Route to add item
@inventory_bp.route('/addItem', methods=['POST'])
def add_item_route():
    data = request.get_json()
    print(f"Received data: {data}")
    try:
        Item.addItem(data['name'], data['quantity'], datetime.strptime(data['date_added'], "%Y-%m-%d"), datetime.strptime(data['usable_until'], "%Y-%m-%d"), data['category'], os.path.join(current_app.config['IMG_URL'], 'placeholder.png'))
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@inventory_bp.route('/updateItem', methods=['POST'])
def update_item_route():
    data = request.get_json()
    print(f"Updating item: {data}")
    try:
        Item.update_item(data['id'], data['name'], data['quantity'], data['category'],  datetime.strptime(data['date_added'], "%Y-%m-%d"), datetime.strptime(data['usable_until'], "%Y-%m-%d"))
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Route to delete item
@inventory_bp.route('/deleteItem', methods=['POST'])
def delete_item_route():
    data = request.get_json()
    ids = data.get('ids', [])
    print(f"Deleting items with ids: {ids}")
    try:
        for id in ids:
            print("Deleting item " + id)
            Item.deleteItemByID(int(id))
        return jsonify({'status': 'success'})
    except Exception as e:
        print(str(e))
        return jsonify({'status': 'error', 'message': str(e)})
