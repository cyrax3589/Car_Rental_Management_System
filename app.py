import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"  # disables oneDNN logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"   # suppresses TF warnings & info

from flask import Flask, render_template, request, jsonify, flash, url_for, redirect, session, g
from mysql.connector import pooling
from datetime import datetime, timedelta
from functools import wraps
import logging
import mysql
from dotenv import load_dotenv
import requests
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import uuid




# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))

# RAG model for chatbot
try:
    with open("combined_knowledge_base.json", "r") as f:
        knowledge_data = json.load(f)
    
    if not isinstance(knowledge_data, list):
        raise ValueError("Knowledge base must be a list of question-answer pairs")
    
    questions = [item["question"] for item in knowledge_data]
    answers = [item["answer"] for item in knowledge_data]
except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
    logging.error(f"Error loading knowledge base: {str(e)}")
    questions = []
    answers = []

# Load embedding model
embedder = SentenceTransformer('all-MiniLM-L6-v2')
if questions:  # Only encode if we have questions
    question_embeddings = embedder.encode(questions)
    
    # Build FAISS index
    index = faiss.IndexFlatL2(question_embeddings.shape[1])
    index.add(np.array(question_embeddings))
else:
    # Create empty index with correct dimensions
    index = faiss.IndexFlatL2(embedder.get_sentence_embedding_dimension())

# RAG pipeline
def get_context(user_input):
    if not questions:
        return None
        
    user_embedding = embedder.encode([user_input])
    distances, indices = index.search(np.array(user_embedding), k=1)
    
    # Add distance threshold to ensure relevant matches
    if distances[0][0] < 2.0:  # Adjust threshold as needed
        return answers[indices[0][0]]
    return None

def generate_response(user_input):
    context = get_context(user_input)
    
    if context:
        response = f"{context}"
    else:
        response = "I apologize, but I don't have specific information about that. Please contact our customer service for more detailed assistance."
    
    return response

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Update this if you have set a password
    'database': 'car_rental',
    'port': 3306,
    'pool_name': 'mypool',
    'pool_size': 5
}

# Initialize the connection pool
connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)

# Database connection decorator
def db_connection(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            conn = connection_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            result = f(cursor, conn, *args, **kwargs)
            cursor.close()
            conn.close()
            return result
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return jsonify({"error": "Database connection error"}), 500
    return decorated_function

@app.route('/healthz')
def health_check():
    try:
        # Test DB connection
        test_conn = connection_pool.get_connection()
        test_conn.close()
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/admin')
def admin_page():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login_page'))
    return redirect(url_for('admin_dashboard'))

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            if request.is_json:
                return jsonify({"error": "Admin access required"}), 403
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login_page')
def admin_login_page():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/admin_login.html')  # Updated template path

@app.route('/admin/login', methods=['GET', 'POST'])
@db_connection
def admin_login(cursor, conn):
    if request.method == 'GET':
        return redirect(url_for('admin_login_page'))
    
    data = request.json if request.is_json else request.form
    
    if not data or 'username' not in data or 'password' not in data:
        flash("Username and password are required", "error")
        return redirect(url_for('admin_login_page'))

    cursor.execute("""
        SELECT * FROM Admins 
        WHERE username = %s AND password = SHA2(%s, 256)
    """, (data['username'], data['password']))
    
    admin = cursor.fetchone()
    if admin:
        session['is_admin'] = True
        session['admin_username'] = admin['username']
        return redirect(url_for('admin_dashboard'))
    
    flash("Invalid credentials", "error")
    return redirect(url_for('admin_login_page'))

@app.route('/admin/dashboard')
@admin_required
@db_connection
def admin_dashboard(cursor, conn):
    try:
        # Get total revenue
        cursor.execute("SELECT COALESCE(SUM(total_cost), 0) as total FROM Rentals")
        total_revenue = cursor.fetchone()['total']

        # Get active rentals count
        cursor.execute("SELECT COUNT(*) as count FROM Rentals WHERE status = 'Ongoing'")
        active_rentals = cursor.fetchone()['count']

        # Get available cars count
        cursor.execute("SELECT COUNT(*) as count FROM Cars WHERE status = 'Available'")
        available_cars = cursor.fetchone()['count']

        # Get total cars
        cursor.execute("SELECT COUNT(*) as count FROM Cars")
        total_cars = cursor.fetchone()['count']

        # Get recent activities
        cursor.execute("""
            SELECT 
                r.start_date as date,
                CONCAT(c.first_name, ' ', c.last_name) as customer,
                CONCAT(cars.make, ' ', cars.model) as car,
                r.status as action
            FROM Rentals r
            JOIN Customers c ON r.customer_id = c.customer_id
            JOIN Cars cars ON r.car_id = cars.car_id
            ORDER BY r.rental_id DESC
            LIMIT 5
        """)
        recent_activities = cursor.fetchall()

        stats = {
            'total_revenue': "{:.2f}".format(float(total_revenue)),
            'active_rentals': active_rentals,
            'available_cars': available_cars,
            'total_cars': total_cars
        }

        return render_template('admin/admin_dashboard.html', 
                             stats=stats,
                             recent_activities=recent_activities)
    except Exception as e:
        logging.error(f"Admin dashboard error: {str(e)}")
        return jsonify({"error": "Failed to load dashboard"}), 500
    

@app.route('/customers', methods=['GET', 'POST'])
@db_connection
def manage_customers(cursor, conn):
    if request.method == 'GET':
        cursor.execute("SELECT * FROM Customers")
        return jsonify(cursor.fetchall())
    
    if request.method == 'POST':
        data = request.json
        required_fields = ['first_name', 'last_name', 'email', 'phone', 'address']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        cursor.execute("""
            INSERT INTO Customers (first_name, last_name, email, phone, address) 
            VALUES (%s, %s, %s, %s, %s)
        """, (data['first_name'], data['last_name'], data['email'], data['phone'], data['address']))
        conn.commit()
        return jsonify({"message": "Customer added successfully", "id": cursor.lastrowid})

@app.route('/login', methods=['GET', 'POST'])
@db_connection
def login(cursor, conn):
    try:
        if request.method == 'GET':
            return render_template('login.html')
        
        data = request.form  # Changed from request.json to only use form data
        
        if not data or 'email' not in data or 'password' not in data:
            flash("Email and password are required", "error")
            return redirect(url_for('login'))

        cursor.execute("""
            SELECT * FROM Customers 
            WHERE email = %s AND password = SHA2(%s, 256)
        """, (data['email'], data['password']))
        
        customer = cursor.fetchone()
        if customer:
            session['customer_id'] = customer['customer_id']
            session['customer_name'] = f"{customer['first_name']} {customer['last_name']}"
            
            if 'remember' in data:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            
            return redirect(url_for('home'))  # Changed from serve_frontend to home
        
        flash("Invalid email or password", "error")
        return redirect(url_for('login'))
        
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        flash("An error occurred during login. Please try again.", "error")
        return redirect(url_for('login'))

@app.route('/cars', methods=['GET'])
@db_connection
def cars(cursor, conn):
    make = request.args.get('make')
    sort = request.args.get('sort')

    query = "SELECT * FROM cars"
    filters = []
    params = []

    if make:
        filters.append("make = %s")
        params.append(make)

    if filters:
        query += " WHERE " + " AND ".join(filters)

    # Build the ORDER BY clause
    order_by_clauses = ["CASE status WHEN 'Available' THEN 0 ELSE 1 END"]  # ensures Available cars come first

    if sort == "price_asc":
        order_by_clauses.append("price_per_day ASC")
    elif sort == "price_desc":
        order_by_clauses.append("price_per_day DESC")
    elif sort == "status":
        order_by_clauses.append("status ASC")

    if order_by_clauses:
        query += " ORDER BY " + ", ".join(order_by_clauses)

    cursor.execute(query, tuple(params))
    cars = cursor.fetchall()

    # Get distinct makes for filter dropdown
    cursor.execute("SELECT DISTINCT make FROM cars")
    makes = [row['make'] for row in cursor.fetchall()]

    selected_make = make
    selected_sort = sort

    return render_template(
        'cars.html',
        cars=cars,
        makes=makes,
        selected_make=selected_make,
        selected_sort=selected_sort
    )




@app.route('/rentals', methods=['POST'])
@db_connection
def rent_car(cursor, conn):
    data = request.json
    required_fields = ['car_id', 'customer_id', 'start_date', 'end_date']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        start_date = datetime.strptime(data['start_date'], "%Y-%m-%d")
        end_date = datetime.strptime(data['end_date'], "%Y-%m-%d")
        days = (end_date - start_date).days
        if days < 1:
            return jsonify({"error": "Invalid date range"}), 400

        # Use transaction for atomic operations
        cursor.execute("START TRANSACTION")
        
        cursor.execute("SELECT price_per_day, status FROM Cars WHERE car_id = %s FOR UPDATE", (data['car_id'],))
        car = cursor.fetchone()
        if not car:
            cursor.execute("ROLLBACK")
            return jsonify({"error": "Car not found"}), 404
        if car['status'] != 'Available':
            cursor.execute("ROLLBACK")
            return jsonify({"error": "Car is not available"}), 400

        total_cost = car['price_per_day'] * days

        cursor.execute("""
            INSERT INTO Rentals (customer_id, car_id, start_date, end_date, total_cost, status) 
            VALUES (%s, %s, %s, %s, %s, 'Ongoing')
        """, (data['customer_id'], data['car_id'], data['start_date'], data['end_date'], total_cost))

        cursor.execute("UPDATE Cars SET status = 'Rented' WHERE car_id = %s", (data['car_id'],))
        
        cursor.execute("COMMIT")
        return jsonify({"message": "Car rented successfully", "total_cost": total_cost, "rental_id": cursor.lastrowid})

    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

def calculate_points(amount):
    # 1 point per $100
    return int(amount / 100)

@app.route('/complete_rental/<int:rental_id>', methods=['POST'])
@db_connection
def complete_rental(cursor, conn, rental_id):
    if not session.get('customer_id'):
        return jsonify({"error": "You must be logged in"}), 401
    
    try:
        # Check if rental belongs to the logged-in customer
        cursor.execute("""
            SELECT r.*, c.car_id 
            FROM Rentals r
            JOIN Cars c ON r.car_id = c.car_id
            WHERE r.rental_id = %s AND r.customer_id = %s AND r.status = 'Ongoing'
        """, (rental_id, session['customer_id']))
        
        rental = cursor.fetchone()
        if not rental:
            return jsonify({"error": "Rental not found or already completed"}), 404
        
        # ... rest of the try block ...
        
        return jsonify({
            "message": "Rental completed successfully",
            "points_earned": points_earned
        }), 200
    
    except Exception as e:
        cursor.execute("ROLLBACK")
        logging.error(f"Error completing rental: {str(e)}")
        return jsonify({"error": "Failed to complete rental"}), 500

@app.route('/admin/complete_rental/<int:rental_id>', methods=['POST'])
@admin_required
@db_connection
def admin_complete_rental(cursor, conn, rental_id):
    try:
        # Get rental information
        cursor.execute("""
            SELECT r.*, c.car_id 
            FROM Rentals r
            JOIN Cars c ON r.car_id = c.car_id
            WHERE r.rental_id = %s AND r.status = 'Ongoing'
        """, (rental_id,))
        
        rental = cursor.fetchone()
        if not rental:
            return jsonify({"error": "Rental not found or already completed"}), 404
        
        # Start transaction
        cursor.execute("START TRANSACTION")
        
        try:
            # Update rental status
            cursor.execute("""
                UPDATE Rentals 
                SET status = 'Completed' 
                WHERE rental_id = %s
            """, (rental_id,))
            
            # Update car status
            cursor.execute("""
                UPDATE Cars 
                SET status = 'Available' 
                WHERE car_id = %s
            """, (rental['car_id'],))
            
            # Calculate points (1 point per $100)
            points_earned = int(rental['total_cost'] / 100)
            
            # Update or insert customer points - remove tier from INSERT/UPDATE
            cursor.execute("""
                INSERT INTO CustomerPoints (customer_id, points)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE 
                    points = points + VALUES(points),
                    last_updated = CURRENT_TIMESTAMP
            """, (rental['customer_id'], points_earned))
            
            # Add to reward history
            cursor.execute("""
                INSERT INTO RewardHistory 
                (customer_id, points_earned, transaction_type, description)
                VALUES (%s, %s, 'RENTAL', 'Points earned from rental completion (admin)')
            """, (rental['customer_id'], points_earned))
            
            conn.commit()
            
            return jsonify({
                "message": "Rental completed successfully",
                "points_earned": points_earned
            }), 200
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e
            
    except Exception as e:
        logging.error(f"Error completing rental: {str(e)}")
        return jsonify({"error": "Failed to complete rental"}), 500


@app.route('/admin/cancel_rental/<int:rental_id>', methods=['POST'])
@admin_required
@db_connection
def admin_cancel_rental(cursor, conn, rental_id):
    try:
        # Get rental information
        cursor.execute("""
            SELECT r.*, c.car_id 
            FROM Rentals r
            JOIN Cars c ON r.car_id = c.car_id
            WHERE r.rental_id = %s AND r.status = 'Ongoing'
        """, (rental_id,))
        
        rental = cursor.fetchone()
        if not rental:
            return jsonify({"error": "Rental not found or already completed/cancelled"}), 404
        
        # Update rental status
        cursor.execute("""
            UPDATE Rentals 
            SET status = 'Cancelled' 
            WHERE rental_id = %s
        """, (rental_id,))
        
        # Update car status
        cursor.execute("""
            UPDATE Cars 
            SET status = 'Available' 
            WHERE car_id = %s
        """, (rental['car_id'],))
        
        conn.commit()
        
        return jsonify({"message": "Rental cancelled successfully"}), 200
    
    except Exception as e:
        logging.error(f"Error cancelling rental: {str(e)}")
        return jsonify({"error": "Failed to cancel rental"}), 500


@app.route('/home')
def home():
    return render_template('home.html')

# Update the root route to redirect to home
@app.route('/')
def root():
    return redirect(url_for('home'))




def calculate_tier(points):
    if points >= 1000:
        return 'Gold'
    elif points >= 500:
        return 'Silver'
    else:
        return 'Bronze'

def calculate_points(amount):
    # 1 point per ₹100
    return int(amount / 100)

@app.route('/rewards')
@db_connection
def rewards(cursor, conn):
    customer_id = session.get('customer_id')
    
    # Get customer points
    cursor.execute("""
        SELECT cp.*, c.first_name, c.last_name 
        FROM CustomerPoints cp
        JOIN Customers c ON cp.customer_id = c.customer_id
        WHERE cp.customer_id = %s
    """, (customer_id,))
    
    points_data = cursor.fetchone()
    if not points_data:
        # Initialize points if not exists - remove tier from INSERT
        cursor.execute("""
            INSERT INTO CustomerPoints (customer_id, points)
            VALUES (%s, 0)
        """, (customer_id,))
        conn.commit()
        points_data = {'points': 0, 'tier': 'Bronze'}

    # Get reward history
    cursor.execute("""
        SELECT * FROM RewardHistory
        WHERE customer_id = %s
        ORDER BY created_at DESC
        LIMIT 10
    """, (customer_id,))
    history = cursor.fetchall()

    # Calculate progress to next tier
    current_points = points_data['points']
    next_tier_points = 500 if current_points < 500 else 1000
    progress = (current_points / next_tier_points) * 100 if current_points < 1000 else 100

    return render_template('rewards.html',
                         points_data=points_data,
                         history=history,
                         progress=progress,
                         next_tier_points=next_tier_points)


@app.route('/admin/customers')
@admin_required
@db_connection
def admin_view_customers(cursor, conn):
    cursor.execute("SELECT * FROM Customers")
    customers = cursor.fetchall()
    return render_template('admin/customers.html', customers=customers)

@app.route('/admin/add_customer')
@admin_required
def admin_add_customer():
    # Redirect to the existing register page
    return redirect(url_for('register'))

@app.route('/admin/manage_cars')
@admin_required
@db_connection
def admin_manage_cars(cursor, conn):
    cursor.execute("SELECT * FROM Cars")
    cars = cursor.fetchall()
    return render_template('admin/cars.html', cars=cars)

@app.route('/admin/active_rentals')
@admin_required
@db_connection
def admin_active_rentals(cursor, conn):
    cursor.execute("""
        SELECT r.*, c.first_name, c.last_name, cars.make, cars.model
        FROM Rentals r
        JOIN Customers c ON r.customer_id = c.customer_id
        JOIN Cars cars ON r.car_id = cars.car_id
        WHERE r.status = 'Ongoing'
    """)
    rentals = cursor.fetchall()
    return render_template('admin/active_rentals.html', rentals=rentals)

@app.route('/admin/rental_history')
@admin_required
@db_connection
def rental_history(cursor, conn):
    cursor.execute("""
        SELECT r.*, c.first_name, c.last_name, cars.make, cars.model
        FROM Rentals r
        JOIN Customers c ON r.customer_id = c.customer_id
        JOIN Cars cars ON r.car_id = cars.car_id
        ORDER BY r.rental_id DESC
    """)
    rentals = cursor.fetchall()
    return render_template('admin/rental_history.html', rentals=rentals)

@app.route('/admin/statistics')
@admin_required
@db_connection
def get_statistics(cursor, conn):
    try:
        # Get monthly revenue data
        cursor.execute("""
            SELECT DATE_FORMAT(start_date, '%Y-%m') as month, 
                   SUM(total_cost) as revenue
            FROM Rentals
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """)
        revenue_results = cursor.fetchall() or []
        revenue_data = {
            'labels': [],
            'datasets': [{
                'label': 'Monthly Revenue',
                'data': [],
                'borderColor': 'rgb(75, 192, 192)',
                'tension': 0.1
            }]
        }
        for row in revenue_results:
            revenue_data['labels'].append(row['month'])
            revenue_data['datasets'][0]['data'].append(float(row['revenue']))

        # Get rental status distribution
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM Rentals
            GROUP BY status
        """)
        status_results = cursor.fetchall() or []
        status_data = {
            'labels': [row['status'] for row in status_results],
            'datasets': [{
                'data': [row['count'] for row in status_results],
                'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56']
            }]
        }

        # Get popular cars
        cursor.execute("""
            SELECT CONCAT(c.make, ' ', c.model) as car,
                   COUNT(*) as rental_count
            FROM Rentals r
            JOIN Cars c ON r.car_id = c.car_id
            GROUP BY c.car_id
            ORDER BY rental_count DESC
            LIMIT 5
        """)
        popular_cars_results = cursor.fetchall() or []
        popular_cars_data = {
            'labels': [row['car'] for row in popular_cars_results],
            'datasets': [{
                'label': 'Number of Rentals',
                'data': [row['rental_count'] for row in popular_cars_results],
                'backgroundColor': 'rgba(54, 162, 235, 0.5)'
            }]
        }

        # Get customer growth - handle if created_at column doesn't exist
        try:
            cursor.execute("""
                SELECT DATE_FORMAT(created_at, '%Y-%m') as month,
                       COUNT(*) as new_customers
                FROM Customers
                GROUP BY month
                ORDER BY month DESC
                LIMIT 12
            """)
            growth_results = cursor.fetchall() or []
        except Exception:
            # Fallback if created_at doesn't exist
            growth_results = []
            
        customer_growth_data = {
            'labels': [row.get('month', '') for row in growth_results],
            'datasets': [{
                'label': 'New Customers',
                'data': [row.get('new_customers', 0) for row in growth_results],
                'borderColor': 'rgb(153, 102, 255)',
                'tension': 0.1
            }]
        }

        return render_template('admin/statistics.html',
                             revenue_data=revenue_data,
                             status_data=status_data,
                             popular_cars_data=popular_cars_data,
                             customer_growth_data=customer_growth_data)
                             
    except Exception as e:
        logging.error(f"Statistics error: {str(e)}")
        # Return empty data if there's an error
        empty_chart_data = {
            'labels': [],
            'datasets': [{'data': [], 'label': 'No Data'}]
        }
        return render_template('admin/statistics.html',
                             revenue_data=empty_chart_data,
                             status_data=empty_chart_data,
                             popular_cars_data=empty_chart_data,
                             customer_growth_data=empty_chart_data)

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    flash('Successfully logged out', 'success')
    return redirect(url_for('admin_login_page'))

@app.route('/admin/search', methods=['POST'])
@admin_required
@db_connection
def admin_search(cursor, conn):
    data = request.json
    search_term = f"%{data['search']}%"
    
    if data['type'] == 'customers':
        cursor.execute("""
            SELECT * FROM Customers 
            WHERE first_name LIKE %s 
            OR last_name LIKE %s 
            OR email LIKE %s
        """, (search_term, search_term, search_term))
    elif data['type'] == 'cars':
        cursor.execute("""
            SELECT * FROM Cars 
            WHERE model LIKE %s 
            OR status LIKE %s
        """, (search_term, search_term))
    elif data['type'] == 'rentals':
        cursor.execute("""
            SELECT r.*, c.first_name, c.last_name, cars.model
            FROM Rentals r
            JOIN Customers c ON r.customer_id = c.customer_id
            JOIN Cars cars ON r.car_id = cars.car_id
            WHERE c.first_name LIKE %s 
            OR c.last_name LIKE %s 
            OR cars.model LIKE %s
        """, (search_term, search_term, search_term))
    
    return jsonify(cursor.fetchall())


@app.route('/register', methods=['GET', 'POST'])
@db_connection
def register(cursor, conn):
    if request.method == 'GET':
        return render_template('register.html')
    
    data = request.json if request.is_json else request.form
    required_fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'password']
    
    if not all(field in data for field in required_fields):
        flash("All fields are required", "error")
        return redirect(url_for('register'))

    try:
        cursor.execute("""
            INSERT INTO Customers (first_name, last_name, email, phone, address, password) 
            VALUES (%s, %s, %s, %s, %s, SHA2(%s, 256))
        """, (data['first_name'], data['last_name'], data['email'], 
              data['phone'], data['address'], data['password']))
        conn.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    except mysql.connector.IntegrityError as e:
        if 'Duplicate entry' in str(e):
            flash("Email already registered", "error")
        else:
            flash("Registration failed", "error")
        return redirect(url_for('register'))


@app.route('/rent/<int:car_id>', methods=['GET', 'POST'])
@db_connection
def rent_page(cursor, conn, car_id):
    if not session.get('customer_id'):
        flash('Please login to rent a car', 'error')
        return redirect(url_for('login'))
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT * FROM Cars 
                WHERE car_id = %s AND status = 'Available'
            """, (car_id,))
            car = cursor.fetchone()
            
            if not car:
                flash("Car is not available for rent", "error")
                return redirect(url_for('cars'))
                
            today = datetime.now().strftime('%Y-%m-%d')
            return render_template('rent_form.html', car=car, today=today)
            
        elif request.method == 'POST':
            data = request.form
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
            
            if start_date >= end_date:
                flash("End date must be after start date", "error")
                return redirect(url_for('rent_page', car_id=car_id))
            
            cursor.execute("SELECT price_per_day FROM Cars WHERE car_id = %s AND status = 'Available'", (car_id,))
            car = cursor.fetchone()
            
            if not car:
                flash("Car is not available for rent", "error")
                return redirect(url_for('cars'))
            
            days = (end_date - start_date).days
            total_cost = car['price_per_day'] * days
            
            cursor.execute("""
                INSERT INTO Rentals (customer_id, car_id, start_date, end_date, total_cost, status)
                VALUES (%s, %s, %s, %s, %s, 'Ongoing')
            """, (session['customer_id'], car_id, start_date, end_date, total_cost))
            
            cursor.execute("UPDATE Cars SET status = 'Rented' WHERE car_id = %s", (car_id,))
            conn.commit()
            
            # More professional success message
            flash("Your vehicle reservation has been confirmed. Thank you for choosing our service!", "success")
            return redirect(url_for('cars'))
            
    except Exception as e:
        logging.error(f"Error in rent_page: {str(e)}")
        flash("An error occurred while processing your request", "error")
        return redirect(url_for('cars'))


@app.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    if request.method == 'GET':
        return render_template('password_reset.html')
    # Add password reset logic here
    return render_template('password_reset.html')


@app.route('/admin/delete_customer/<int:customer_id>', methods=['DELETE'])
@admin_required
@db_connection
def admin_delete_customer(cursor, conn, customer_id):
    try:
        # Check if customer has active rentals
        cursor.execute("SELECT COUNT(*) as count FROM Rentals WHERE customer_id = %s AND status = 'Ongoing'", (customer_id,))
        active_rentals = cursor.fetchone()['count']
        
        if active_rentals > 0:
            return jsonify({"error": "Cannot delete customer with active rentals"}), 400
            
        # Delete customer
        cursor.execute("DELETE FROM Customers WHERE customer_id = %s", (customer_id,))
        conn.commit()
        
        return jsonify({"message": "Customer deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting customer: {str(e)}")
        return jsonify({"error": "Failed to delete customer"}), 500


@app.route('/profile')
@db_connection
def profile(cursor, conn):
    if not session.get('customer_id'):
        return redirect(url_for('login'))
        
    try:
        # Get customer details
        cursor.execute("""
            SELECT * FROM Customers 
            WHERE customer_id = %s
        """, (session['customer_id'],))
        customer = cursor.fetchone()
        
        # Get active rentals
        cursor.execute("""
            SELECT r.*, c.make, c.model, c.registration_number
            FROM Rentals r
            JOIN Cars c ON r.car_id = c.car_id
            WHERE r.customer_id = %s AND r.status = 'Ongoing'
            ORDER BY r.start_date DESC
        """, (session['customer_id'],))
        active_rentals = cursor.fetchall()
        
        # Get rental history
        cursor.execute("""
            SELECT r.*, c.make, c.model, c.registration_number
            FROM Rentals r
            JOIN Cars c ON r.car_id = c.car_id
            WHERE r.customer_id = %s AND r.status != 'Ongoing'
            ORDER BY r.start_date DESC
        """, (session['customer_id'],))
        rental_history = cursor.fetchall()
        
        return render_template('profile.html', 
                             customer=customer,
                             active_rentals=active_rentals,
                             rental_history=rental_history)
                             
    except Exception as e:
        logging.error(f"Profile error: {str(e)}")
        flash("Error loading profile", "error")
        return redirect(url_for('home'))

@app.route('/policy', methods=['GET', 'POST'])
def policy():
    return render_template('policy.html')

@app.route('/terms', methods=['GET', 'POST'])
def terms():
    return render_template('terms.html')

@app.route('/disclaimer', methods=['GET', 'POST'])
def disclaimer():
    return render_template('disclaimer.html')

@app.route('/FAQs', methods=['GET', 'POST'])
def FAQs():
    return render_template('FAQs.html')

@app.route('/about_us', methods=['GET', 'POST'])
def about_us():
    return render_template('about_us.html')

@app.route('/blogs', methods=['GET', 'POST'])
def blogs():
    return render_template('blogs.html')

@app.route('/blog1', methods=['GET', 'POST'])
def blog1():
    return render_template('blog1.html')

@app.route('/blog2', methods=['GET', 'POST'])
def blog2():
    return render_template('blog2.html')

@app.route('/blog3', methods=['GET', 'POST'])
def blog3():
    return render_template('blog3.html')


@app.route('/edit_profile', methods=['GET', 'POST'])
@db_connection
def edit_profile(cursor, conn):
    if not session.get('customer_id'):
        return redirect(url_for('login'))
    
    customer_id = session['customer_id']
    
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        new_password = request.form.get('new_password')
        
        if new_password:
            cursor.execute("""
                UPDATE Customers 
                SET first_name=%s, last_name=%s, email=%s, phone=%s, address=%s, password=SHA2(%s, 256)
                WHERE customer_id=%s
            """, (first_name, last_name, email, phone, address, new_password, customer_id))
        else:
            cursor.execute("""
                UPDATE Customers 
                SET first_name=%s, last_name=%s, email=%s, phone=%s, address=%s 
                WHERE customer_id=%s
            """, (first_name, last_name, email, phone, address, customer_id))
        
        conn.commit()
        
        # Update session with combined first and last name
        session['customer_name'] = f"{first_name} {last_name}"
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('home'))
    
    # GET request - show the form
    cursor.execute("SELECT * FROM Customers WHERE customer_id = %s", (customer_id,))
    customer = cursor.fetchone()
    
    return render_template('edit_profile.html', customer=customer)




# Define the RAG chatbot route
@app.route('/RAG_chatbot', methods=['POST'])
def rag_chatbot():
    data = request.get_json()
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({'reply': 'Please enter a message.'})

    try:
        # Use our RAG model
        bot_response = generate_response(user_message)
        return jsonify({'reply': bot_response})
    except Exception as e:
        logging.error(f"Chatbot error: {str(e)}")
        return jsonify({'reply': "I apologize, but I'm having trouble processing your request right now."})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/admin/cars', methods=['POST', 'PUT', 'DELETE'])
@admin_required
@db_connection
def manage_cars(cursor, conn):
    if request.method == 'POST':
        data = request.json
        required_fields = ['model', 'make', 'year', 'registration_number', 'price_per_day', 'status']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        cursor.execute("""
            INSERT INTO Cars (model, make, year, registration_number, price_per_day, status) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (data['model'], data['make'], data['year'], data['registration_number'], data['price_per_day'], data['status']))
        conn.commit()
        return jsonify({"message": "Car added successfully", "id": cursor.lastrowid})

    if request.method == 'PUT':
        data = request.json
        cursor.execute("""
            UPDATE Cars 
            SET model = %s, make = %s, year = %s, registration_number = %s, price_per_day = %s, status = %s 
            WHERE car_id = %s
        """, (data['model'], data['make'], data['year'], data['registration_number'], data['price_per_day'], data['status'], data['car_id']))
        conn.commit()
        return jsonify({"message": "Car updated successfully"})

    if request.method == 'DELETE':
        car_id = request.args.get('car_id')
        cursor.execute("DELETE FROM Cars WHERE car_id = %s", (car_id,))
        conn.commit()
        return jsonify({"message": "Car deleted successfully"})
    

    
@app.route('/payments', methods=['GET', 'POST'])
@db_connection
def payments(cursor, conn):
    if not session.get('customer_id'):
        flash('Please login to rent a car', 'error')
        return redirect(url_for('login'))
    
    # For GET requests, redirect to cars page
    if request.method == 'GET':
        return redirect(url_for('cars'))
    
    # For POST requests, render the payments page
    return render_template('payments.html')

@app.route('/confirm_booking', methods=['POST'])
@db_connection
def confirm_booking(cursor, conn):
    if not session.get('customer_id'):
        flash('Please login to rent a car', 'error')
        return redirect(url_for('login'))
    
    try:
        # Get form data
        car_id = request.form.get('car_id')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        payment_method = request.form.get('payment_method')
        customer_id = session.get('customer_id')
        
        # Validate data
        if not all([car_id, start_date, end_date, payment_method, customer_id]):
            flash("Missing required information", "error")
            return redirect(url_for('cars'))
        
        # Convert dates
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Calculate rental duration and cost
        cursor.execute("SELECT price_per_day FROM Cars WHERE car_id = %s AND status = 'Available'", (car_id,))
        car = cursor.fetchone()
        
        if not car:
            flash("Car is not available for rent", "error")
            return redirect(url_for('cars'))
        
        days = (end_date - start_date).days
        total_cost = days * car['price_per_day']
        
        # Insert rental record
        cursor.execute("""
            INSERT INTO Rentals (customer_id, car_id, start_date, end_date, total_cost, status) 
            VALUES (%s, %s, %s, %s, %s, 'Ongoing')
        """, (customer_id, car_id, start_date, end_date, total_cost))
        
        # Update car status
        cursor.execute("UPDATE Cars SET status = 'Rented' WHERE car_id = %s", (car_id,))
        
        conn.commit()
        
        flash("Booking confirmed successfully!", "success")
        return redirect(url_for('cars'))
        
    except Exception as e:
        conn.rollback()
        flash(f"Error confirming booking: {str(e)}", "error")
        return redirect(url_for('cars'))



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=10000, debug=True, use_reloader=False)
