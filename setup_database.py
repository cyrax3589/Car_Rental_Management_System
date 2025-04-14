import mysql.connector
from mysql.connector import Error

# Database configuration
db_config = {
    'host': 'sql12.freesqldatabase.com',
    'user': 'sql12773048',
    'password': 'RyyudkihXb',
    'port': 3306
}

def setup_database():
    try:
        # First connect without database to create it
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS sql12773048")
        cursor.execute("USE sql12773048")
        
        # Execute schema creation
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Drop existing tables
        tables = ["Payments", "Rentals", "Cars", "Customers", "Admins"]
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # Create tables
        tables_creation = """
        CREATE TABLE IF NOT EXISTS Customers (
            customer_id INT PRIMARY KEY AUTO_INCREMENT,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            phone VARCHAR(15),
            address VARCHAR(255)
        );

        CREATE TABLE IF NOT EXISTS Admins (
            admin_id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Cars (
            car_id INT PRIMARY KEY AUTO_INCREMENT,
            model VARCHAR(50),
            make VARCHAR(50),
            year INT,
            registration_number VARCHAR(20) UNIQUE,
            status ENUM('Available', 'Rented', 'Under Maintenance') DEFAULT 'Available',
            price_per_day DECIMAL(10, 2)
        );

        CREATE TABLE IF NOT EXISTS Rentals (
            rental_id INT PRIMARY KEY AUTO_INCREMENT,
            customer_id INT,
            car_id INT,
            start_date DATE,
            end_date DATE,
            total_cost DECIMAL(10, 2),
            status ENUM('Ongoing', 'Completed', 'Cancelled') DEFAULT 'Ongoing',
            FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE,
            FOREIGN KEY (car_id) REFERENCES Cars(car_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Payments (
            payment_id INT PRIMARY KEY AUTO_INCREMENT,
            rental_id INT,
            amount DECIMAL(10, 2),
            payment_date DATE,
            payment_method VARCHAR(50),
            FOREIGN KEY (rental_id) REFERENCES Rentals(rental_id) ON DELETE CASCADE
        );
        """
        
        for statement in tables_creation.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        # Insert initial data
        cursor.execute("INSERT INTO Admins (username, password) VALUES ('superadmin', SHA2('Admin@123', 256)), ('admin', SHA2('admin123', 256))")
        
        # Insert sample cars
        cars_data = """
        INSERT INTO Cars (model, make, year, registration_number, status, price_per_day)
        VALUES 
            ('M4 Competition', 'BMW', 2024, 'BMW001', 'Available', 890.00),
            ('Model S Plaid', 'Tesla', 2024, 'TSL001', 'Available', 950.00),
            ('911 GT3 RS', 'Porsche', 2024, 'POR001', 'Available', 1200.00),
            ('G63 AMG', 'Mercedes', 2024, 'MER001', 'Available', 1100.00),
            ('Civic', 'Honda', 2023, 'ABC123', 'Available', 50.00),
            ('Corolla', 'Toyota', 2022, 'DEF456', 'Available', 45.00),
            ('Mustang GT', 'Ford', 2024, 'DEF001', 'Available', 590.00),
            ('RS7', 'Audi', 2024, 'AUD001', 'Available', 850.00),
            ('Urus', 'Lamborghini', 2024, 'LAM001', 'Available', 1500.00),
            ('SF90', 'Ferrari', 2024, 'FER001', 'Available', 2000.00)
        """
        cursor.execute(cars_data)
        
        # Add new cars from the image
        new_cars = """
        INSERT INTO Cars (model, make, year, registration_number, status, price_per_day)
        VALUES 
            ('M4', 'BMW', 2024, 'BMW2024', 'Available', 150.00),
            ('Model S', 'Tesla', 2024, 'TSL2024', 'Available', 180.00),
            ('911', 'Porsche', 2024, 'POR2024', 'Available', 200.00)
        """
        cursor.execute(new_cars)
        
        connection.commit()
        print("Database setup completed successfully!")
        
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    setup_database()