from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError
import os

from database import (
    create_tables,
    create_user,
    get_user,
    get_all_products,
    search_products,
    add_product,
    update_product,
    delete_product,
    create_order,
    get_user_orders,
    get_dashboard,
    get_all_orders
)


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="E-Commerce Store API",
    version="3.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE STARTUP
# =========================================================

@app.on_event("startup")
def startup_event():
    create_tables()


# =========================================================
# JWT SETTINGS
# =========================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "development-secret-change-this"
)

ALGORITHM = "HS256"

security = HTTPBearer()


# =========================================================
# AUTH
# =========================================================

def create_token(user_id, username, role):

    payload = {
        "user_id": user_id,
        "username": username,
        "role": role
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token."
        )


def require_admin(
    user=Depends(get_current_user)
):

    if user.get("role") != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admin access required."
        )

    return user


# =========================================================
# MODELS
# =========================================================

class SignupData(BaseModel):
    username: str
    password: str


class LoginData(BaseModel):
    username: str
    password: str


class ProductData(BaseModel):
    name: str
    price: float
    stock: int


class CartItem(BaseModel):
    product_id: int
    quantity: int


class CheckoutData(BaseModel):
    items: list[CartItem]


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "E-Commerce Store API is running"
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "message": "Backend is running"
    }


# =========================================================
# SIGNUP
# =========================================================

@app.post("/signup")
def signup(user: SignupData):

    username = user.username.strip()

    if len(username) < 3:

        raise HTTPException(
            status_code=400,
            detail="Username must contain at least 3 characters."
        )

    if len(user.password) < 6:

        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters."
        )

    user_id = create_user(
        username,
        user.password
    )

    if user_id is None:

        raise HTTPException(
            status_code=409,
            detail="Username already exists."
        )

    return {
        "message": "Account created successfully."
    }


# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login(user: LoginData):

    result = get_user(
        user.username.strip(),
        user.password
    )

    if result is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password."
        )

    token = create_token(
        result[0],
        result[1],
        result[2]
    )

    return {
        "message": "Login successful.",
        "token": token,
        "user_id": result[0],
        "username": result[1],
        "role": result[2]
    }


# =========================================================
# PRODUCTS
# =========================================================

@app.get("/products")
def products(
    user=Depends(get_current_user)
):

    return get_all_products()


@app.get("/products/search/{name}")
def search(
    name: str,
    user=Depends(get_current_user)
):

    return search_products(name)


# =========================================================
# ADMIN ADD
# =========================================================

@app.post("/products")
def create_product(
    product: ProductData,
    user=Depends(require_admin)
):

    name = product.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Product name is required."
        )

    if product.price < 0:
        raise HTTPException(
            status_code=400,
            detail="Price cannot be negative."
        )

    if product.stock < 0:
        raise HTTPException(
            status_code=400,
            detail="Stock cannot be negative."
        )

    product_id = add_product(
        name,
        product.price,
        product.stock
    )

    return {
        "message": "Product added successfully.",
        "id": product_id
    }


# =========================================================
# ADMIN UPDATE
# =========================================================

@app.put("/products/{product_id}")
def edit_product(
    product_id: int,
    product: ProductData,
    user=Depends(require_admin)
):

    name = product.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Product name is required."
        )

    if product.price < 0:
        raise HTTPException(
            status_code=400,
            detail="Price cannot be negative."
        )

    if product.stock < 0:
        raise HTTPException(
            status_code=400,
            detail="Stock cannot be negative."
        )

    updated = update_product(
        product_id,
        name,
        product.price,
        product.stock
    )

    if updated == 0:
        raise HTTPException(
            status_code=404,
            detail="Product not found."
        )

    return {
        "message": "Product updated successfully."
    }


# =========================================================
# ADMIN DELETE
# =========================================================

@app.delete("/products/{product_id}")
def remove_product(
    product_id: int,
    user=Depends(require_admin)
):

    deleted = delete_product(product_id)

    if deleted == 0:
        raise HTTPException(
            status_code=404,
            detail="Product not found."
        )

    return {
        "message": "Product deleted successfully."
    }


# =========================================================
# CHECKOUT
# =========================================================

@app.post("/checkout")
def checkout(
    order: CheckoutData,
    user=Depends(get_current_user)
):

    if not order.items:

        raise HTTPException(
            status_code=400,
            detail="Cart is empty."
        )

    cart = [
        {
            "product_id": item.product_id,
            "quantity": item.quantity
        }
        for item in order.items
    ]

    try:

        result = create_order(
            user["user_id"],
            cart
        )

        return {
            "message": "Order placed successfully.",
            "order_id": result["order_id"],
            "total": result["total"]
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# =========================================================
# USER ORDERS
# =========================================================

@app.get("/orders/me")
def my_orders(
    user=Depends(get_current_user)
):

    return get_user_orders(
        user["user_id"]
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.get("/dashboard")
def dashboard(
    user=Depends(require_admin)
):

    return get_dashboard()


# =========================================================
# ADMIN ORDERS
# =========================================================

@app.get("/orders")
def all_orders(
    user=Depends(require_admin)
):

    return get_all_orders()
