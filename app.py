from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from dateutil import parser
import requests
import json
import os
from config import SPOONACULAR_API_KEY
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# Set up the database with absolute path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'groceries.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('GroceryItem', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class GroceryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    expiry_date = db.Column(db.DateTime, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), default='Other')
    notes = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

def get_recipes_for_ingredient(ingredient):
    base_url = "https://api.spoonacular.com/recipes/findByIngredients"
    
    try:
        params = {
            "apiKey": SPOONACULAR_API_KEY,
            "ingredients": ingredient,
            "number": 3,
            "ranking": 2,
            "ignorePantry": True
        }
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def init_db():
    try:
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Drop all tables and recreate them
        with app.app_context():
            db.drop_all()
            db.create_all()
            
            # Create test user
            test_user = User(username='testuser', email='test@example.com')
            test_user.set_password('testpass123')
            db.session.add(test_user)
            db.session.commit()
            
            # Add sample grocery items
            sample_items = [
                GroceryItem(
                    name='Milk',
                    category='Dairy',
                    quantity=1,
                    expiry_date=datetime.now() + timedelta(days=7),
                    notes='Whole milk',
                    user_id=test_user.id
                ),
                GroceryItem(
                    name='Chicken Breast',
                    category='Meat',
                    quantity=2,
                    expiry_date=datetime.now() + timedelta(days=3),
                    notes='Fresh, for curry',
                    user_id=test_user.id
                ),
                GroceryItem(
                    name='Spinach',
                    category='Vegetables',
                    quantity=1,
                    expiry_date=datetime.now() + timedelta(days=4),
                    notes='Organic baby spinach',
                    user_id=test_user.id
                ),
                GroceryItem(
                    name='Yogurt',
                    category='Dairy',
                    quantity=3,
                    expiry_date=datetime.now() + timedelta(days=10),
                    notes='Greek yogurt',
                    user_id=test_user.id
                ),
                GroceryItem(
                    name='Tomatoes',
                    category='Vegetables',
                    quantity=6,
                    expiry_date=datetime.now() + timedelta(days=5),
                    notes='Roma tomatoes',
                    user_id=test_user.id
                )
            ]
            
            for item in sample_items:
                db.session.add(item)
            db.session.commit()
            
            print("Database initialized successfully with sample data!")
    except Exception as e:
        print(f"Error initializing database: {e}")

# Initialize the database
init_db()

def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            
            user = User.query.filter_by(username=username).first()
            print(f"Login attempt for user: {username}")
            
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['username'] = user.username
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('An error occurred during login.', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    sort_by = request.args.get('sort', 'expiry')
    items = GroceryItem.query.filter_by(user_id=session['user_id'])
    
    if sort_by == 'name':
        items = items.order_by(GroceryItem.name)
    elif sort_by == 'category':
        items = items.order_by(GroceryItem.category, GroceryItem.expiry_date)
    else:  # sort by expiry
        items = items.order_by(GroceryItem.expiry_date)
    
    items = items.all()
    
    expiring_soon = [item for item in items if (item.expiry_date - datetime.now()).days <= 3]
    recipes = {}
    if SPOONACULAR_API_KEY != "YOUR_API_KEY_HERE":
        for item in expiring_soon[:3]:
            recipes[item.id] = get_recipes_for_ingredient(item.name)
    
    categories = db.session.query(GroceryItem.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    stats = {
        'total_items': len(items),
        'expiring_soon': len([i for i in items if (i.expiry_date - datetime.now()).days <= 7]),
        'expired': len([i for i in items if (i.expiry_date - datetime.now()).days < 0])
    }
    
    return render_template('index.html', 
                         items=items, 
                         now=datetime.now(),
                         recipes=recipes,
                         categories=categories,
                         stats=stats)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        expiry_date = parser.parse(request.form['expiry_date'])
        category = request.form['category']
        notes = request.form['notes']
        
        item = GroceryItem(
            name=name, 
            quantity=quantity, 
            expiry_date=expiry_date,
            category=category,
            notes=notes,
            user_id=session['user_id']
        )
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('index'))
    
    categories = ['Fruits & Vegetables', 'Dairy', 'Meat & Fish', 'Pantry', 'Frozen', 'Other']
    return render_template('add.html', categories=categories)

@app.route('/delete/<int:id>')
@login_required
def delete_item(id):
    item = GroceryItem.query.get_or_404(id)
    if item.user_id != session['user_id']:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('index'))
    
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    item = GroceryItem.query.get_or_404(id)
    if item.user_id != session['user_id']:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        item.name = request.form['name']
        item.quantity = int(request.form['quantity'])
        item.expiry_date = parser.parse(request.form['expiry_date'])
        item.category = request.form['category']
        item.notes = request.form['notes']
        db.session.commit()
        return redirect(url_for('index'))
    
    categories = ['Fruits & Vegetables', 'Dairy', 'Meat & Fish', 'Pantry', 'Frozen', 'Other']
    return render_template('edit.html', item=item, categories=categories)

@app.route('/toggle_quantity/<int:id>/<action>')
@login_required
def toggle_quantity(id, action):
    item = GroceryItem.query.get_or_404(id)
    if item.user_id != session['user_id']:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('index'))
    
    if action == 'increase':
        item.quantity += 1
    elif action == 'decrease' and item.quantity > 1:
        item.quantity -= 1
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
else:
    # When running in production, initialize the database
    with app.app_context():
        db.create_all()
