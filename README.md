# StockWise — Inventory Management System

StockWise is a full-stack inventory management application built to help users manage products, track stock movements, and identify low-stock items.

## Live Demo

- **Frontend:** https://stockwise-ashen-one.vercel.app
- **Backend API:** https://stockwise-gs2r.onrender.com
- **API Documentation:** https://stockwise-gs2r.onrender.com/docs

## Features

- Add, view, update, and delete products
- Track stock-in and stock-out movements
- Prevent stock-out operations when available quantity is insufficient
- Identify products with low inventory
- View inventory summary statistics
- Store product and stock movement data in PostgreSQL
- Validate API requests and handle errors

## Tech Stack

**Frontend:** React, Vite, JavaScript, CSS

**Backend:** Python, FastAPI, Pydantic

**Database:** PostgreSQL

**Database Driver:** Psycopg

**Deployment:** Vercel, Render

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/nikhilkhade18/StockWise.git
cd StockWise
```

### 2. Set up the backend

Create and activate a Python virtual environment, then install dependencies:

```bash
python -m venv .venv
pip install -r requirements.txt
```

Configure your PostgreSQL connection using the environment variables supported in `db.py`. Set `DB_PASSWORD` securely in your terminal rather than committing credentials.

Start the API:

```bash
python -m uvicorn main:app --reload
```

Open the API documentation at http://127.0.0.1:8000/docs.

### 3. Set up the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

For local development, the frontend uses `http://127.0.0.1:8000` as its default API URL. You can override it with the `VITE_API_URL` environment variable.

## Testing

Backend tests are available in `test_main.py`.

Run the test suite with:

```bash
pytest -q
```

## Future Improvements

- User authentication and role-based access
- Inventory alerts and reporting
- Automated deployment checks and expanded test coverage

## Author

**Nikhil Khade**

GitHub: https://github.com/nikhilkhade18
