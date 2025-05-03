import mysql.connector

# Database connection configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Update this if you have set a password
    'database': 'car_rental',
    'port': 3306
}

# Car data to insert
cars_data = [
    ('EV6 GT', 'Kia', 2024, 'E1V2G', 'Available', 250.00),
    ('Cerato GT', 'Kia', 2024, 'C1T2G', 'Available', 215.00),
    ('Carnival', 'Kia', 2024, 'C1R2L', 'Available', 325.00),
    ('AMG GT', 'Mercedes-Benz', 2024, 'A1M2GT', 'Available', 425.00),
    ('SL-Class', 'Mercedes-Benz', 2024, 'S1L2C', 'Available', 550.00),
    ('PB18 E-Tron', 'Audi', 2024, 'P1B2ET', 'Available', 1050.00),
    ('AI:Trail Quattro', 'Audi', 2024, 'AI1TQ', 'Available', 950.00),
    ('918 Spyder', 'Porche', 2024, 'S1P2DR', 'Available', 650.00),
    ('911 GT3 RS', 'Porche', 2024, 'G1T2RS', 'Available', 400.00),
    ('XUV 700', 'Mahindra', 2024, 'X1UV27', 'Available', 200.00),
    ('XEV 9e', 'Mahindra', 2024, 'X1EV2E', 'Available', 250.00)
]

try:
    # Establish connection to the database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # SQL query for inserting cars
    insert_query = """
    INSERT IGNORE INTO Cars (model, make, year, registration_number, status, price_per_day)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    # Execute the query for each car
    for car in cars_data:
        cursor.execute(insert_query, car)
    
    # Commit the changes
    conn.commit()
    
    print(f"Successfully inserted {cursor.rowcount} cars into the database.")
    
except mysql.connector.Error as err:
    print(f"Error: {err}")
    
finally:
    # Close the cursor and connection
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
    print("Database connection closed.")