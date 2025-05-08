from flask import Flask, jsonify, request
import mysql.connector
from dotenv import load_dotenv
import os
import jwt
import datetime
from functools import wraps
import bcrypt

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Debug: Print environment variables
print("DB_HOST:", os.getenv("DB_HOST"))
print("DB_USER:", os.getenv("DB_USER"))
print("DB_NAME:", os.getenv("DB_NAME"))
print("JWT_SECRET:", os.getenv("JWT_SECRET"))

# MySQL connection (without password)
try:
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),       # MySQL server address
        user=os.getenv("DB_USER"),      # MySQL username
        database=os.getenv("DB_NAME")   # Name of the database
        # No password is provided
    )
    print("Connected to MySQL database!")
except mysql.connector.Error as err:
    print(f"Error: {err}")

# Secret key for JWT
app.config['SECRET_KEY'] = os.getenv("JWT_SECRET")

# Token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated

# Home route
@app.route('/')
def home():
    return "Welcome to the Flask API!"

# Signup route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data['name']
    username = data['username']
    password = data['password']

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO Users (name, username, password) VALUES (%s, %s, %s)", (name, username, hashed_password))
        db.commit()
        return jsonify({"message": "User created successfully"}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        token = jwt.encode({
            'id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        }, app.config['SECRET_KEY'])
        return jsonify({"token": token})
    else:
        return jsonify({"error": "Invalid username or password"}), 401

# Update user route (protected)
@app.route('/users/<int:id>', methods=['PUT'])
@token_required
def update_user(id):
    data = request.get_json()
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')

    cursor = db.cursor()
    try:
        if password:
            # Hash the new password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE Users SET name = %s, username = %s, password = %s WHERE id = %s", (name, username, hashed_password, id))
        else:
            # Update only name and username
            cursor.execute("UPDATE Users SET name = %s, username = %s WHERE id = %s", (name, username, id))
        db.commit()
        return jsonify({"message": "User updated successfully"})
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400

# Add product route (protected)
@app.route('/products', methods=['POST'])
@token_required
def add_product():
    data = request.get_json()
    pname = data['pname']
    description = data['description']
    price = data['price']
    stock = data['stock']

    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO Products (pname, description, price, stock) VALUES (%s, %s, %s, %s)", (pname, description, price, stock))
        db.commit()
        return jsonify({"message": "Product added successfully"}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400

# Get all products route (protected)
@app.route('/products', methods=['GET'])
@token_required
def get_products():
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Products")
        products = cursor.fetchall()
        return jsonify(products)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400

# Get single product route (protected)
@app.route('/products/<int:pid>', methods=['GET'])
@token_required
def get_product(pid):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Products WHERE pid = %s", (pid,))
        product = cursor.fetchone()
        if product:
            return jsonify(product)
        else:
            return jsonify({"error": "Product not found"}), 404
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400

# Update product route (protected)
@app.route('/products/<int:pid>', methods=['PUT'])
@token_required
def update_product(pid):
    data = request.get_json()
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE Products SET pname = %s, description = %s, price = %s, stock = %s WHERE pid = %s", (data['pname'], data['description'], data['price'], data['stock'], pid))
        db.commit()
        return jsonify({"message": "Product updated successfully"})
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400

# Delete product route (protected)
@app.route('/products/<int:pid>', methods=['DELETE'])
@token_required
def delete_product(pid):
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM Products WHERE pid = %s", (pid,))
        db.commit()
        return jsonify({"message": "Product deleted successfully"})
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)