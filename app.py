from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
import google.generativeai as genai
import time 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
model = genai.GenerativeModel('gemini-pro')
genai.configure(api_key="key")



db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    budget = db.Column(db.String(150), nullable = True)
    dietary = db.Column(db.Text, nullable=True)

class GroceryList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('user.id', name='fk_grocerylist_user'), 
        nullable=False
    )
    
    # Relationship to link items
    items = db.relationship('GroceryItem', back_populates='grocery_list', cascade="all, delete-orphan")

class GroceryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(100), nullable=True)
    list_id = db.Column(
        db.Integer, 
        db.ForeignKey('grocery_list.id', name='fk_groceryitem_list'), 
        nullable=False
    )
    # Relationship back to the GroceryList
    grocery_list = db.relationship('GroceryList', back_populates='items')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect('/dashboard')  # Redirect to dashboard if the user is already logged in
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if existing_user.username == username:
                flash('Username is already taken. Please choose a different one.', 'danger')
            if existing_user.email == email:
                flash('Email is already registered. Please choose a different one.', 'danger')
            return render_template('register.html', username=username, email=email)

        # Hash the password and create a new user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)

        # Add user to the database
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', username="", email="")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')  # Flash success message here
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your email and password.', 'danger')

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    grocery_lists = GroceryList.query.filter_by(user_id=current_user.id).all()
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 0,
        "max_output_tokens": 8192,
        }

    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        ]


    model = genai.GenerativeModel(model_name="gemini-pro",
                                    generation_config=generation_config,
                                    safety_settings=safety_settings)

    convo = model.start_chat(history=[])

    return render_template('dashboard.html', 
                           username=current_user.username, 
                           grocery_lists=grocery_lists)

@app.route('/add_list', methods=['POST'])
@login_required
def add_list():
    data = request.json  # Expecting JSON data from the frontend
    list_name = data.get('name')
    items = data.get('items', [])
    
    if not list_name or not items:
        return jsonify({'message': 'List name and items are required'}), 400

    # Create the new grocery list
    new_list = GroceryList(name=list_name, user_id=current_user.id)
    db.session.add(new_list)
    db.session.commit()

    # Add items to the list
    for item in items:
        new_item = GroceryItem(name=item['name'], type=item['type'], list_id=new_list.id)
        db.session.add(new_item)
    
    db.session.commit()

    # Return the list_id in the response for use in the frontend
    return jsonify({'message': 'List saved successfully', 'list_id': new_list.id}), 201

@app.route('/shopping', methods=['GET', 'POST'])
@login_required
def shopping():
    # Fetch all grocery lists for the current user
    return render_template('shopping.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Get the updated profile data
        budget = request.form['budget']
        dietary = request.form['dietary']

        # Update the user's data in the database
        current_user.budget = budget
        current_user.dietary = dietary
        db.session.commit()  # Commit the changes to the database
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))  # Reload the page to show the updated info

    return render_template('profile.html', username=current_user.username, email=current_user.email, budget=current_user.budget, dietary=current_user.dietary)

@app.route('/api/lists', methods=['POST'])
@login_required
def create_list():
    data = request.json
    name = data.get('name')
    items = data.get('items')

    if not name:
        return jsonify({'error': 'List name is required'}), 400
    if not items or len(items) == 0:
        return jsonify({'error': 'At least one item is required'}), 400

    # Create a new grocery list
    new_list = GroceryList(name=name, user_id=current_user.id)
    db.session.add(new_list)
    db.session.commit()

    # Create GroceryItems for each item in the list
    for item in items:
        new_item = GroceryItem(name=item.strip(), list_id=new_list.id)
        db.session.add(new_item)

    db.session.commit()

    return jsonify({
        'id': new_list.id,
        'name': new_list.name,
        'items': [item.name for item in new_list.items]
    })

@app.route('/delete_list/<int:list_id>', methods=['POST'])
@login_required
def delete_list(list_id):
    grocery_list = GroceryList.query.filter_by(id=list_id, user_id=current_user.id).first()
    
    if grocery_list:
        # Delete the list and all its associated items
        db.session.delete(grocery_list)
        db.session.commit()
        flash('List deleted successfully!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('List not found or you do not have permission to delete it.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/most_popular_item', methods=['GET'])
@login_required
def most_popular_item():
    from gemini_api import get_most_popular_item
    """Returns the most popular grocery item across all lists."""
    popular_item = get_most_popular_item()
    return jsonify({"most_popular_item": popular_item})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')  # Flash only the logout message
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure the database is created
    app.run(debug=True)
