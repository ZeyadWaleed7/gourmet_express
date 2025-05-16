from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pyodbc
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc:///?odbc_connect=' + 'DRIVER={SQL Server};SERVER=LAPTOP-BTLK3Q2I;DATABASE=dish drop;Trusted_Connection=yes;'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    User_ID = db.Column(db.Integer, primary_key=True)
    Username = db.Column(db.String(255), unique=True, nullable=False)
    Password = db.Column(db.String(255), nullable=False)
    Account = db.relationship('Account', backref='user', uselist=False)
    Customer = db.relationship('Customer', backref='user', uselist=False)

class Customer(db.Model):
    __tablename__ = 'Customer'
    Customer_ID = db.Column(db.Integer, primary_key=True)
    User_ID = db.Column(db.Integer, db.ForeignKey('Users.User_ID'))
    Phone_Number = db.Column(db.BigInteger, unique=True, nullable=False)
    Name = db.Column(db.String(255), nullable=False)
    street_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255), nullable=False)
    Feedback_ID = db.Column(db.Integer, db.ForeignKey('Feedback.Feedback_ID'))

class Restaurant(db.Model):
    __tablename__ = 'Restaurant'
    Restaurant_ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(255), nullable=False)
    Feedback_ID = db.Column(db.Integer, db.ForeignKey('Feedback.Feedback_ID'))

class Product(db.Model):
    __tablename__ = 'Product'
    Product_ID = db.Column(db.Integer, primary_key=True)
    Product_name = db.Column(db.String(255), nullable=False)
    Price = db.Column(db.Float, nullable=False)
    Description = db.Column(db.Text)
    Restaurant_ID = db.Column(db.Integer, db.ForeignKey('Restaurant.Restaurant_ID'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(Username=username).first()
        if user and check_password_hash(user.Password, password):
            login_user(user)
            return redirect(url_for('restaurant_start'))
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            street_address = request.form['street_address']
            city = request.form['city']

            # Create new user
            hashed_password = generate_password_hash(password)
            new_user = User(Username=username, Password=hashed_password)
            db.session.add(new_user)
            db.session.flush()

            # Create customer profile
            new_customer = Customer(
                User_ID=new_user.User_ID,
                Name=name,
                Phone_Number=phone,
                street_address=street_address,
                city=city
            )
            db.session.add(new_customer)
            db.session.commit()

            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Restaurant routes
@app.route('/restaurants')
def get_restaurants():
    restaurants = Restaurant.query.all()
    return jsonify([{
        'id': r.Restaurant_ID,
        'name': r.Name
    } for r in restaurants])

@app.route('/restaurant/<int:restaurant_id>/menu')
def get_restaurant_menu(restaurant_id):
    products = Product.query.filter_by(Restaurant_ID=restaurant_id).all()
    return jsonify([{
        'id': p.Product_ID,
        'name': p.Product_name,
        'price': p.Price,
        'description': p.Description
    } for p in products])

# Cart and Order routes
@app.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    try:
        product_id = request.json.get('product_id')
        quantity = request.json.get('quantity', 1)
        
        # Add to cart logic here
        return jsonify({'message': 'Product added to cart'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/cart')
@login_required
def view_cart():
    # Get cart items logic here
    return render_template('cart.html')

@app.route('/order/create', methods=['POST'])
@login_required
def create_order():
    try:
        # Create order logic here
        return jsonify({'message': 'Order created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
