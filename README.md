# 🛒 E-Commerce Store

A full-stack e-commerce application built using Python, FastAPI, SQLite, JWT authentication, and Streamlit.

## Features

### User
- Signup
- Login
- JWT authentication
- Browse products
- Search products
- Select quantity
- Add to cart
- View cart total
- Checkout
- Automatic stock reduction
- Order history

### Admin
- Admin login
- Dashboard
- Add products
- Update products
- Delete products
- Change price
- Change stock
- View orders
- View total sales
- View low-stock products

## Technologies

- Python
- FastAPI
- Streamlit
- SQLite
- JWT
- python-jose
- cryptography
- Requests

## Project Structure

```text
ecommers/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── requirements.txt
│   └── products.db
│
├── frontend/
│   ├── app.py
│   ├── background.png
│   └── requirements.txt
│
├── .gitignore
└── README.md