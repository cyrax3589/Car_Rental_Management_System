-- Active: 1742929688092@@127.0.0.1@3306@car_rental
    CREATE DATABASE car_rental;
    USE car_rental;
-- Remove duplicate CREATE TABLE and ALTER statements
DROP TABLE IF EXISTS Customers;
-- First drop tables with foreign key dependencies
DROP TABLE IF EXISTS Payments;
DROP TABLE IF EXISTS Rentals;
DROP TABLE IF EXISTS Customers;
DROP TABLE IF EXISTS Admins;

-- Then create the Customers table
CREATE TABLE Customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    address VARCHAR(255)
);

CREATE TABLE Admins (
    admin_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE Cars (
    car_id INT PRIMARY KEY AUTO_INCREMENT,
    model VARCHAR(50),
    make VARCHAR(50),
    year INT,
    registration_number VARCHAR(20) UNIQUE,
    status ENUM('Available', 'Rented', 'Under Maintenance') DEFAULT 'Available',
    price_per_day DECIMAL(10, 2)
);

CREATE TABLE Rentals (
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

CREATE TABLE Payments (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    rental_id INT,
    amount DECIMAL(10, 2),
    payment_date DATE,
    payment_method VARCHAR(50),
    FOREIGN KEY (rental_id) REFERENCES Rentals(rental_id) ON DELETE CASCADE
);

-- Insert initial data
INSERT INTO Admins (username, password) VALUES ('admin', SHA2('admin123', 256));

-- Insert sample cars
INSERT INTO Cars (model, make, year, registration_number, status, price_per_day)
VALUES 
    ('Civic', 'Honda', 2023, 'ABC123', 'Available', 50.00),
    ('Corolla', 'Toyota', 2022, 'DEF456', 'Available', 45.00),
    ('Mustang GT', 'Ford', 2024, 'DEF001', 'Available', 590.00);