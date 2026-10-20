
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import psycopg
from db import get_connection

app = FastAPI(title="StockWise API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://stockwise-ashen-one.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# 1. Create database tables when the app starts
@app.on_event("startup")
def create_tables():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    price NUMERIC(10, 2) NOT NULL CHECK (price > 0),
                    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER NOT NULL
                        REFERENCES products(id) ON DELETE RESTRICT,
                    movement_type VARCHAR(10) NOT NULL
                        CHECK (movement_type IN ('IN', 'OUT')),
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)


# 2. Request models
class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)
    quantity: int = Field(ge=0)


class StockIn(BaseModel):
    quantity: int = Field(gt=0)


class StockOut(BaseModel):
    quantity: int = Field(gt=0)


# 3. Convert a database row to a JSON-friendly dictionary
def product_to_dict(product):
    return {
        "id": product[0],
        "name": product[1],
        "price": float(product[2]),
        "quantity": product[3],
    }


# 4. Home endpoint
@app.get("/")
def home():
    return {"message": "Welcome to StockWise API"}


# 5. Get all products
@app.get("/products")
def get_products():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, price, quantity
                FROM products
                ORDER BY id
            """)
            products = cur.fetchall()

    return [product_to_dict(p) for p in products]


# 6. Create a product
@app.post("/products", status_code=201)
def create_product(request: ProductCreate):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO products (name, price, quantity)
                VALUES (%s, %s, %s)
                RETURNING id, name, price, quantity
            """, (request.name, request.price, request.quantity))
            product = cur.fetchone()

    return product_to_dict(product)


# 7. Low-stock products
@app.get("/products/low-stock")
def get_low_stock_products():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, price, quantity
                FROM products
                WHERE quantity < 5
                ORDER BY quantity ASC
            """)
            products = cur.fetchall()

    return [product_to_dict(p) for p in products]


# 8. Inventory summary
@app.get("/summary")
def get_inventory_summary():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*),
                    COALESCE(SUM(quantity), 0),
                    COUNT(*) FILTER (WHERE quantity < 5)
                FROM products
            """)
            summary = cur.fetchone()

    return {
        "total_products": summary[0],
        "total_units": summary[1],
        "low_stock_count": summary[2],
    }


# 9. Stock movement history
@app.get("/products/{product_id}/history")
def get_stock_history(product_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM products WHERE id = %s",
                (product_id,),
            )
            if cur.fetchone() is None:
                raise HTTPException(
                    status_code=404,
                    detail="Product not found",
                )

            cur.execute("""
                SELECT movement_type, quantity, created_at
                FROM stock_movements
                WHERE product_id = %s
                ORDER BY created_at DESC
            """, (product_id,))
            history = cur.fetchall()

    return [
        {
            "movement_type": row[0],
            "quantity": row[1],
            "created_at": row[2],
        }
        for row in history
    ]


# 10. Get one product
@app.get("/products/{product_id}")
def get_product(product_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, price, quantity
                FROM products
                WHERE id = %s
            """, (product_id,))
            product = cur.fetchone()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product_to_dict(product)


# 11. Update a product
@app.put("/products/{product_id}")
def update_product(product_id: int, request: ProductCreate):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE products
                SET name = %s, price = %s, quantity = %s
                WHERE id = %s
                RETURNING id, name, price, quantity
            """, (
                request.name,
                request.price,
                request.quantity,
                product_id,
            ))
            product = cur.fetchone()

            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail="Product not found",
                )

    return product_to_dict(product)


# 12. Delete a product
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM products WHERE id = %s RETURNING id",
                    (product_id,),
                )
                deleted = cur.fetchone()

                if deleted is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Product not found",
                    )

    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete product because stock history exists",
        )

    return {"message": "Product deleted successfully"}


# 13. Stock in
@app.post("/products/{product_id}/stock-in")
def stock_in_product(product_id: int, request: StockIn):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE products
                SET quantity = quantity + %s
                WHERE id = %s
                RETURNING id, name, quantity
            """, (request.quantity, product_id))
            product = cur.fetchone()

            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail="Product not found",
                )

            cur.execute("""
                INSERT INTO stock_movements
                    (product_id, movement_type, quantity)
                VALUES (%s, %s, %s)
            """, (product_id, "IN", request.quantity))

    return {
        "message": "Stock added successfully",
        "product_id": product[0],
        "name": product[1],
        "remaining_stock": product[2],
    }


# 14. Stock out
@app.post("/products/{product_id}/stock-out")
def stock_out_product(product_id: int, request: StockOut):
    with get_connection() as conn:
        with conn.cursor() as cur:
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
                    (product_id,),
                )
                exists = cur.fetchone()

                if exists is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Product not found",
                    )

                raise HTTPException(
                    status_code=400,
                    detail="Insufficient stock",
                )

            cur.execute("""
                INSERT INTO stock_movements
                    (product_id, movement_type, quantity)
                VALUES (%s, %s, %s)
            """, (product_id, "OUT", request.quantity))

    return {
        "message": "Stock updated successfully",
        "product_id": product[0],
        "name": product[1],
        "remaining_stock": product[2],
    }
