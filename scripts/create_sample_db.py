"""
Create a sample e-commerce database for testing the NLP-to-SQL system.
This database contains customers, products, orders, and order items.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

# Sample data
FIRST_NAMES = ["John", "Jane", "Bob", "Alice", "Charlie", "Emma", "David", "Sarah", "Michael", "Lisa"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor"]
CITIES = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego"]
STATES = ["NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA"]

PRODUCT_CATEGORIES = ["Electronics", "Clothing", "Books", "Home & Garden", "Sports", "Toys"]
PRODUCTS = {
    "Electronics": ["Laptop", "Smartphone", "Tablet", "Headphones", "Smart Watch", "Camera"],
    "Clothing": ["T-Shirt", "Jeans", "Jacket", "Sneakers", "Dress", "Sweater"],
    "Books": ["Fiction Novel", "Cookbook", "Biography", "Science Book", "Mystery Novel", "Self-Help Book"],
    "Home & Garden": ["Coffee Maker", "Blender", "Vacuum Cleaner", "Garden Tools", "Decorative Lamp", "Cookware Set"],
    "Sports": ["Running Shoes", "Yoga Mat", "Dumbbells", "Tennis Racket", "Basketball", "Bicycle"],
    "Toys": ["Board Game", "Puzzle", "Action Figure", "Doll", "Building Blocks", "RC Car"]
}

def create_database():
    """Create and populate the sample database."""
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    db_path = "data/ecommerce.db"
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    print("Creating tables...")
    
    # Customers table
    cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            city TEXT,
            state TEXT,
            registration_date DATE NOT NULL
        )
    """)
    
    # Products table
    cursor.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            stock_quantity INTEGER NOT NULL,
            description TEXT
        )
    """)
    
    # Orders table
    cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_date DATE NOT NULL,
            status TEXT NOT NULL,
            total_amount DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    
    # Order items table
    cursor.execute("""
        CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)
    
    print("Populating customers...")
    # Insert customers
    customers = []
    for i in range(50):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        email = f"{first_name.lower()}.{last_name.lower()}{i}@email.com"
        phone = f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        city_idx = random.randint(0, len(CITIES) - 1)
        city = CITIES[city_idx]
        state = STATES[city_idx]
        reg_date = (datetime.now() - timedelta(days=random.randint(30, 730))).strftime("%Y-%m-%d")
        
        cursor.execute("""
            INSERT INTO customers (first_name, last_name, email, phone, city, state, registration_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, email, phone, city, state, reg_date))
        customers.append(cursor.lastrowid)
    
    print("Populating products...")
    # Insert products
    products = []
    for category, product_list in PRODUCTS.items():
        for product_name in product_list:
            price = round(random.uniform(9.99, 999.99), 2)
            stock = random.randint(0, 200)
            description = f"High-quality {product_name.lower()} from the {category} category"
            
            cursor.execute("""
                INSERT INTO products (product_name, category, price, stock_quantity, description)
                VALUES (?, ?, ?, ?, ?)
            """, (product_name, category, price, stock, description))
            products.append(cursor.lastrowid)
    
    print("Populating orders and order items...")
    # Insert orders and order items
    statuses = ["Pending", "Completed", "Shipped", "Delivered", "Cancelled"]
    
    for i in range(100):
        customer_id = random.choice(customers)
        order_date = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
        status = random.choice(statuses)
        
        # Create order with placeholder total
        cursor.execute("""
            INSERT INTO orders (customer_id, order_date, status, total_amount)
            VALUES (?, ?, ?, ?)
        """, (customer_id, order_date, status, 0.0))
        order_id = cursor.lastrowid
        
        # Add 1-5 items to the order
        num_items = random.randint(1, 5)
        total_amount = 0.0
        
        selected_products = random.sample(products, min(num_items, len(products)))
        for product_id in selected_products:
            # Get product price
            cursor.execute("SELECT price FROM products WHERE product_id = ?", (product_id,))
            unit_price = cursor.fetchone()[0]
            
            quantity = random.randint(1, 3)
            total_amount += unit_price * quantity
            
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
            """, (order_id, product_id, quantity, unit_price))
        
        # Update order total
        cursor.execute("""
            UPDATE orders SET total_amount = ? WHERE order_id = ?
        """, (round(total_amount, 2), order_id))
    
    # Commit and close
    conn.commit()
    
    # Print summary
    print("\n" + "="*50)
    print("Database created successfully!")
    print("="*50)
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    print(f"Customers: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM products")
    print(f"Products: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    print(f"Orders: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM order_items")
    print(f"Order Items: {cursor.fetchone()[0]}")
    
    print(f"\nDatabase location: {os.path.abspath(db_path)}")
    print("="*50)
    
    conn.close()

if __name__ == "__main__":
    create_database()
