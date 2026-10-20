
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to StockWise API"
    }


def test_create_product():
    response = client.post(
        "/products",
        json={
            "name": "Test Mouse",
            "price": 500,
            "quantity": 10
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Mouse"
    assert data["quantity"] == 10


def test_create_product_invalid_price():
    response = client.post(
        "/products",
        json={
            "name": "Invalid Product",
            "price": -100,
            "quantity": 5
        }
    )

    assert response.status_code == 422


def test_get_missing_product():
    response = client.get("/products/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_stock_out_insufficient_stock():
    response = client.post(
        "/products/999999/stock-out",
        json={"quantity": 1}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"




def test_stock_out_insufficient_stock():
    create_response = client.post(
        "/products",
        json={
            "name": "Low Stock Test",
            "price": 100,
            "quantity": 2
        }
    )

    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    response = client.post(
        f"/products/{product_id}/stock-out",
        json={"quantity": 5}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient stock"
    product_response = client.get(
        f"/products/{product_id}"
    )

    assert product_response.status_code == 200
    assert product_response.json()["quantity"] == 2



def test_stock_in_increases_quantity():
    create_response = client.post(
        "/products",
        json={
            "name": "Stock In Test",
            "price": 100,
            "quantity": 3
        }
    )
    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.post(
        f"/products/{product_id}/stock-in",
        json={"quantity": 4}
    )

    assert response.status_code == 200
    assert response.json()["remaining_stock"] == 7

    history_response = client.get(
        f"/products/{product_id}/history"
    )

    assert history_response.status_code == 200
    assert history_response.json()[0]["movement_type"] == "IN"
    assert history_response.json()[0]["quantity"] == 4


def test_stock_out_decreases_quantity():
    create_response = client.post(
        "/products",
        json={
            "name": "Stock Out Test",
            "price": 100,
            "quantity": 10
        }
    )
    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.post(
        f"/products/{product_id}/stock-out",
        json={"quantity": 3}
    )

    assert response.status_code == 200
    assert response.json()["remaining_stock"] == 7

    history_response = client.get(
        f"/products/{product_id}/history"
    )

    assert history_response.status_code == 200
    assert history_response.json()[0]["movement_type"] == "OUT"
    assert history_response.json()[0]["quantity"] == 3



def test_stock_in_invalid_quantity():
    create_response = client.post(
        "/products",
        json={
            "name": "Validation Test",
            "price": 100,
            "quantity": 5
        }
    )
    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.post(
        f"/products/{product_id}/stock-in",
        json={"quantity": 0}
    )

    assert response.status_code == 422

    product_response = client.get(f"/products/{product_id}")
    assert product_response.json()["quantity"] == 5


def test_summary_endpoint():
    create_response = client.post(
        "/products",
        json={
            "name": "Summary Test Product",
            "price": 200,
            "quantity": 2
        }
    )
    assert create_response.status_code == 201

    response = client.get("/summary")

    assert response.status_code == 200

    data = response.json()
    assert "total_products" in data
    assert "total_units" in data
    assert "low_stock_count" in data
    assert data["total_products"] >= 1
    assert data["total_units"] >= 2
    assert data["low_stock_count"] >= 1


def test_low_stock_endpoint():
    create_response = client.post(
        "/products",
        json={
            "name": "Low Stock Endpoint Test",
            "price": 100,
            "quantity": 2
        }
    )
    assert create_response.status_code == 201

    response = client.get("/products/low-stock")

    assert response.status_code == 200
    assert any(
        product["id"] == create_response.json()["id"]
        for product in response.json()
    )


def test_update_product():
    create_response = client.post(
        "/products",
        json={
            "name": "Update Test Product",
            "price": 100,
            "quantity": 5
        }
    )
    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.put(
        f"/products/{product_id}",
        json={
            "name": "Updated Product",
            "price": 250,
            "quantity": 8
        }
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Product"
    assert float(response.json()["price"]) == 250
    assert response.json()["quantity"] == 8


def test_delete_product():
    create_response = client.post(
        "/products",
        json={
            "name": "Delete Test Product",
            "price": 100,
            "quantity": 5
        }
    )
    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.delete(f"/products/{product_id}")

    assert response.status_code in (200, 204)

    get_response = client.get(f"/products/{product_id}")
    assert get_response.status_code == 404


def test_stock_movement_history():
    create_response = client.post(
        "/products",
        json={
            "name": "History Test Product",
            "price": 100,
            "quantity": 10
        }
    )
    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    stock_in_response = client.post(
        f"/products/{product_id}/stock-in",
        json={"quantity": 4}
    )
    assert stock_in_response.status_code == 200

    stock_out_response = client.post(
        f"/products/{product_id}/stock-out",
        json={"quantity": 3}
    )
    assert stock_out_response.status_code == 200

    response = client.get(f"/products/{product_id}/history")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["movement_type"] == "OUT"
    assert response.json()[0]["quantity"] == 3
    assert response.json()[1]["movement_type"] == "IN"
    assert response.json()[1]["quantity"] == 4
