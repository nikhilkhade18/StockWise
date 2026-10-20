
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import psycopg
import os

app = FastAPI(title="StockWise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 1. Database connection
def get_connection():
    return psycopg.connect(
        host="localhost",
        dbname="stockwise_db",
        user="postgres",
        password=os.getenv("DB_PASSWORD")
    )


# 2. Request models
class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)
    quantity: int = Field(ge=0)


class StockIn(BaseModel):
    quantity: int = Field(gt=0)


class StockOut(BaseModel):
    quantity: int = Field(gt=0)


# Helper: convert database row to JSON-friendly dictionary
def product_to_dict(product):
    return {
        "id": product[0],
        "name": product[1],
        "price": float(product[2]),
        "quantity": product[3]
    }


# 3. Home endpoint
@app.get("/")
def home():
    return {"message": "Welcome to StockWise API"}


# 4. Get all products
@app.get("/products")
def get_products():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, price, quantity
        FROM products
        ORDER BY id
    """)

    products = cur.fetchall()

    cur.close()
    conn.close()

    return [product_to_dict(p) for p in products]


# 5. Create a product
@app.post("/products", status_code=201)
def create_product(request: ProductCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO products (name, price, quantity)
        VALUES (%s, %s, %s)
        RETURNING id, name, price, quantity
    """, (request.name, request.price, request.quantity))

    product = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return product_to_dict(product)


# 6. Low-stock products
# Keep this route above /products/{product_id}
@app.get("/products/low-stock")
def get_low_stock_products():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, price, quantity
        FROM products
        WHERE quantity < 5
        ORDER BY quantity ASC
    """)

    products = cur.fetchall()

    cur.close()
    conn.close()

    return [product_to_dict(p) for p in products]


# 7. Inventory summary
@app.get("/summary")
def get_inventory_summary():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(quantity), 0),
            COUNT(*) FILTER (WHERE quantity < 5)
        FROM products
    """)

    summary = cur.fetchone()

    cur.close()
    conn.close()

    return {
        "total_products": summary[0],
        "total_units": summary[1],
        "low_stock_count": summary[2]
    }


# 8. Stock movement history
@app.get("/products/{product_id}/history")
def get_stock_history(product_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM products WHERE id = %s",
        (product_id,)
    )
    product = cur.fetchone()

    if product is None:
        cur.close()
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    cur.execute("""
        SELECT movement_type, quantity, created_at
        FROM stock_movements
        WHERE product_id = %s
        ORDER BY created_at DESC
    """, (product_id,))

    history = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "movement_type": row[0],
            "quantity": row[1],
            "created_at": row[2]
        }
        for row in history
    ]


# 9. Get one product
@app.get("/products/{product_id}")
def get_product(product_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, price, quantity
        FROM products
        WHERE id = %s
    """, (product_id,))

    product = cur.fetchone()

    cur.close()
    conn.close()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product_to_dict(product)


# 10. Update a product
@app.put("/products/{product_id}")
def update_product(product_id: int, request: ProductCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE products
        SET name = %s, price = %s, quantity = %s
        WHERE id = %s
        RETURNING id, name, price, quantity
    """, (
        request.name,
        request.price,
        request.quantity,
        product_id
    ))

    product = cur.fetchone()

    if product is None:
        cur.close()
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    conn.commit()
    cur.close()
    conn.close()

    return product_to_dict(product)


# 11. Delete a product
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM products WHERE id = %s",
        (product_id,)
    )
    product = cur.fetchone()

    if product is None:
        cur.close()
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    try:
        cur.execute(
            "DELETE FROM products WHERE id = %s",
            (product_id,)
        )
        conn.commit()

    except psycopg.errors.ForeignKeyViolation:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(
            status_code=409,
            detail="Cannot delete product because stock history exists"
        )

    cur.close()
    conn.close()

    return {"message": "Product deleted successfully"}


# 12. Stock in
@app.post("/products/{product_id}/stock-in")
def stock_in_product(product_id: int, request: StockIn):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE products
        SET quantity = quantity + %s
        WHERE id = %s
        RETURNING id, name, quantity
    """, (request.quantity, product_id))

    product = cur.fetchone()

    if product is None:
        cur.close()
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    cur.execute("""
        INSERT INTO stock_movements
            (product_id, movement_type, quantity)
        VALUES (%s, %s, %s)
    """, (product_id, "IN", request.quantity))

    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "Stock added successfully",
        "product_id": product[0],
        "name": product[1],
        "remaining_stock": product[2]
    }


# 13. Stock out
@app.post("/products/{product_id}/stock-out")
def stock_out_product(product_id: int, request: StockOut):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE products
        SET quantity = quantity - %s
        WHERE id = %s AND quantity >= %s
        RETURNING id, name, quantity
    """, (request.quantity, product_id, request.quantity))

    product = cur.fetchone()

    if product is None:
        cur.execute(
            "SELECT id FROM products WHERE id = %s",
            (product_id,)
        )
        exists = cur.fetchone()

        cur.close()
        conn.close()

        if exists is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    cur.execute("""
        INSERT INTO stock_movements
            (product_id, movement_type, quantity)
        VALUES (%s, %s, %s)
    """, (product_id, "OUT", request.quantity))

    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "Stock updated successfully",
        "product_id": product[0],
        "name": product[1],
        "remaining_stock": product[2]
    }
