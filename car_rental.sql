-- Active: 1744720891582@@127.0.0.1@3306@car_rental
-- First check if tables exist and drop them in correct order

CREATE DATABASE IF NOT EXISTS car_rental;

USE car_rental;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS RewardHistory;
DROP TABLE IF EXISTS CustomerPoints;
DROP TABLE IF EXISTS Payments;
DROP TABLE IF EXISTS Rentals;
DROP TABLE IF EXISTS Cars;
DROP TABLE IF EXISTS Customers;
DROP TABLE IF EXISTS Admins;

SET FOREIGN_KEY_CHECKS = 1;

-- Then create the tables
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

-- Insert initial data (only if not exists)
INSERT IGNORE INTO Admins (username, password) VALUES ('admin', SHA2('admin123', 256));

-- Insert sample cars (only if not exists)
INSERT IGNORE INTO Cars (model, make, year, registration_number, status, price_per_day)
VALUES 
    ('M4', 'BMW', 2024, 'BMW001', 'Available', 150.00),
    ('Model S', 'Tesla', 2024, 'TSL001', 'Available', 180.00),
    ('911', 'Porsche', 2024, 'POR001', 'Available', 200.00),
    ('A8', 'Audi', 2024, 'AUD001', 'Available', 170.00),
    ('S-Class', 'Mercedes-Benz', 2024, 'MER001', 'Available', 190.00),
    ('Model 3', 'Tesla', 2023, 'TSL002', 'Available', 120.00),
    ('M3', 'BMW', 2023, 'BMW002', 'Available', 140.00),
    ('Cayenne', 'Porsche', 2023, 'POR002', 'Available', 160.00),
    ('Q7', 'Audi', 2023, 'AUD002', 'Available', 150.00),
    ('GLS', 'Mercedes-Benz', 2023, 'MER002', 'Available', 170.00),
    ('Civic Type R', 'Honda', 2024, 'HON001', 'Available', 100.00),
    ('Supra', 'Toyota', 2024, 'TOY001', 'Available', 130.00),
    ('GT-R', 'Nissan', 2024, 'NIS001', 'Available', 180.00),
    ('RC F', 'Lexus', 2024, 'LEX001', 'Available', 140.00),
    ('Stinger GT', 'Kia', 2024, 'KIA001', 'Available', 90.00);

INSERT IGNORE INTO Cars (model, make, year, registration_number, status, price_per_day)
VALUES 
    ('EV6 GT', 'Kia', 2024, 'E1V2G', 'Available', 250.00),
    ('Cerato GT', 'Kia', 2024, 'C1T2G', 'Available', 215.00),
    ('Carnival', 'Kia', 2024, 'C1R2L', 'Available', 325.00),
    ('AMG GT', 'Mercedes-Benz', 2024, 'A1M2GT', 'Available', 425.00),
    ('SL-Class', 'Mercedes-Benz', 2024, 'S1L2C', 'Available', 550.00),
    ('PB18 E-Tron', 'Audi', 2024, 'P1B2ET', 'Available', 1050.00),
    ('AI:Trail Quattro', 'Audi', 2024, 'AI1TQ', 'Available', 950.00),
    ('918 Spyder', 'Porsche', 2024, 'S1P2DR', 'Available', 650.00),
    ('911 GT3 RS', 'Porsche', 2024, 'G1T2RS', 'Available', 400.00),
    ('XUV 700', 'Mahindra', 2024, 'X1UV27', 'Available', 200.00),
    ('XEV 9e', 'Mahindra', 2024, 'X1EV2E', 'Available', 250.00),

    -- Create CustomerPoints table
CREATE TABLE IF NOT EXISTS CustomerPoints (
    customer_id INT PRIMARY KEY,
    points INT DEFAULT 0,
    tier VARCHAR(10) GENERATED ALWAYS AS (
        CASE 
            WHEN points >= 1000 THEN 'Gold'
            WHEN points >= 500 THEN 'Silver'
            ELSE 'Bronze'
        END
    ) STORED,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
);

-- Create RewardHistory table
CREATE TABLE IF NOT EXISTS RewardHistory (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    points_earned INT,
    transaction_type VARCHAR(20),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
);

select * from car_rental.cars;
