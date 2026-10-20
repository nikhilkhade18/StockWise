import psycopg

conn = psycopg.connect(
    dbname="stockwise_db",
    user="postgres",
    password="12345",
    host="localhost",
    port="5432"
)



cur = conn.cursor()


cur.execute(
    "SELECT id FROM products WHERE name = %s",
    ("Keyboard",)
)

existing_product = cur.fetchone()

if existing_product is None:
    cur.execute(
        """
        INSERT INTO products (name, price, quantity)
        VALUES (%s, %s, %s)
        """,
        ("Keyboard", 800, 10)
    )
    conn.commit()
    print("Product added successfully!")
else:
    print("Product already exists!")



cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        price NUMERIC(10, 2) NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0
    )
""")

conn.commit()


print("Products table created successfully!")


print("StockWise database connected successfully!")


cur.execute("SELECT * FROM products")

products = cur.fetchall()

for product in products:
    print(product)

cur.close()
conn.close()