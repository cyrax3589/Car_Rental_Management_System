
CREATE DATABASE IF NOT EXISTS car_rental;
USE car_rental;



CREATE TABLE IF NOT EXISTS Customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT NOT NULL,
    password VARCHAR(256) NOT NULL
);

CREATE TABLE IF NOT EXISTS Cars (
    car_id INT PRIMARY KEY AUTO_INCREMENT,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    price_per_day DECIMAL(10,2) NOT NULL,
    status ENUM('Available', 'Rented', 'Maintenance') DEFAULT 'Available'
);

CREATE TABLE IF NOT EXISTS Rentals (
    rental_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    car_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_cost DECIMAL(10,2) NOT NULL,
    status ENUM('Ongoing', 'Completed', 'Cancelled') DEFAULT 'Ongoing',
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
    FOREIGN KEY (car_id) REFERENCES Cars(car_id)
);

CREATE TABLE IF NOT EXISTS Admins (
    admin_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(256) NOT NULL
);



SELECT * FROM Customers;