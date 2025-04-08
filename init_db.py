import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

def execute_sql_file():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)
    
    with open('car_rental.sql', 'r') as file:
        # Remove comments and empty lines
        sql_content = '\n'.join(line for line in file if not line.startswith('--') and line.strip())
        sql_commands = sql_content.split(';')
        
        for command in sql_commands:
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                    if cursor.with_rows:
                        cursor.fetchall()  # Clear any results
                    conn.commit()
                except mysql.connector.Error as err:
                    print(f"Error executing command: {err}")
                    print(f"Failed command: {command}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    execute_sql_file()
    print("Database initialization completed!")