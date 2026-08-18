import streamlit as st
import requests
import base64
import os


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="E-Commerce Store",
    page_icon="🛒",
    layout="wide"
)


# =========================================================
# API CONFIGURATION
# =========================================================

API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

# =========================================================
# BACKGROUND
# =========================================================

try:

    with open("background.png", "rb") as file:

        image = base64.b64encode(
            file.read()
        ).decode()

    st.markdown(
        f"""
        <style>

        .stApp {{
            background-image:
                linear-gradient(
                    rgba(0,0,0,0.65),
                    rgba(0,0,0,0.65)
                ),
                url("data:image/png;base64,{image}");

            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        .block-container {{
            background: rgba(0,0,0,0.25);
            border-radius: 18px;
            padding: 2rem;
        }}

        h1, h2, h3, h4 {{
            color: white !important;
            text-shadow: 2px 2px 5px black;
        }}

        p, label, span {{
            color: white !important;
        }}

        .stTextInput input,
        .stNumberInput input {{
            background-color: white !important;
            color: black !important;
        }}

        .stButton > button {{
            background-color: #1565c0 !important;
            color: white !important;
            border: 2px solid white !important;
            font-weight: 700 !important;
        }}

        .stButton > button:hover {{
            background-color: #1e88e5 !important;
            color: white !important;
        }}

        section[data-testid="stSidebar"] {{
            background: rgba(0,0,0,0.92) !important;
        }}

        section[data-testid="stSidebar"] * {{
            color: white !important;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )

except FileNotFoundError:

    pass


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "token" not in st.session_state:
    st.session_state.token = ""

if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = ""

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None


# =========================================================
# LOGIN / SIGNUP
# =========================================================

if not st.session_state.logged_in:

    st.title("🛒 E-Commerce Store")

    login_tab, signup_tab = st.tabs(
        ["🔐 Login", "📝 Create Account"]
    )


    # =====================================================
    # LOGIN
    # =====================================================

    with login_tab:

        username = st.text_input(
            "Username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "🔐 Login",
            type="primary",
            use_container_width=True
        ):

            if username.strip() == "":
                st.error("Please enter your username.")

            elif password == "":
                st.error("Please enter your password.")

            else:

                try:

                    response = requests.post(
                        API_URL + "/login",
                        json={
                            "username": username.strip(),
                            "password": password
                        },
                        timeout=5
                    )

                    if response.status_code == 200:

                        result = response.json()

                        st.session_state.logged_in = True
                        st.session_state.token = result["token"]
                        st.session_state.username = result["username"]
                        st.session_state.role = result["role"]
                        st.session_state.cart = {}

                        st.rerun()

                    else:

                        st.error(
                            response.json()["detail"]
                        )

                except requests.exceptions.ConnectionError:

                    st.error(
                        "FastAPI backend is not running."
                    )


    # =====================================================
    # SIGNUP
    # =====================================================

    with signup_tab:

        username = st.text_input(
            "Choose Username",
            key="signup_username"
        )

        password = st.text_input(
            "Create Password",
            type="password",
            key="signup_password"
        )

        confirm = st.text_input(
            "Confirm Password",
            type="password",
            key="signup_confirm"
        )

        st.caption(
            "Username: minimum 3 characters"
        )

        st.caption(
            "Password: minimum 6 characters"
        )

        if st.button(
            "📝 Create Account",
            type="primary",
            use_container_width=True
        ):

            if len(username.strip()) < 3:

                st.error(
                    "Username must contain at least 3 characters."
                )

            elif len(password) < 6:

                st.error(
                    "Password must contain at least 6 characters."
                )

            elif password != confirm:

                st.error(
                    "Passwords do not match."
                )

            else:

                try:

                    response = requests.post(
                        API_URL + "/signup",
                        json={
                            "username": username.strip(),
                            "password": password
                        },
                        timeout=5
                    )

                    if response.status_code == 200:

                        st.success(
                            "Account created successfully. "
                            "Please login."
                        )

                    else:

                        st.error(
                            response.json()["detail"]
                        )

                except requests.exceptions.ConnectionError:

                    st.error(
                        "FastAPI backend is not running."
                    )

    st.stop()


# =========================================================
# AUTH HEADER
# =========================================================

HEADERS = {
    "Authorization":
        "Bearer " + st.session_state.token
}


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("🛒 E-Commerce")

    st.divider()

    st.write(
        "👤 " + st.session_state.username
    )

    st.write(
        "🔑 " + st.session_state.role
    )

    st.divider()

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.token = ""
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.cart = {}
        st.session_state.edit_id = None

        st.rerun()


# =========================================================
# ADMIN
# =========================================================

if st.session_state.role == "admin":

    st.title("👨‍💼 Admin Dashboard")

    response = requests.get(
        API_URL + "/dashboard",
        headers=HEADERS
    )

    if response.status_code != 200:

        st.error(
            "Unable to load admin dashboard."
        )

        st.stop()

    dashboard = response.json()


    # -----------------------------
    # METRICS
    # -----------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Products",
            dashboard["total_products"]
        )

    with col2:

        st.metric(
            "Current Stock",
            dashboard["total_stock"]
        )

    with col3:

        st.metric(
            "Orders",
            dashboard["total_orders"]
        )

    with col4:

        st.metric(
            "Total Sales",
            "₹" + str(
                round(
                    dashboard["total_sales"],
                    2
                )
            )
        )


    # -----------------------------
    # LOW STOCK
    # -----------------------------

    st.subheader(
        "⚠️ Low Stock"
    )

    if len(dashboard["low_stock"]) == 0:

        st.success(
            "No low-stock products."
        )

    else:

        for product in dashboard["low_stock"]:

            st.write(
                product["name"],
                "- Stock:",
                product["stock"]
            )


    st.divider()


    # =====================================================
    # ADD PRODUCT
    # =====================================================

    st.header("➕ Add Product")

    col1, col2, col3 = st.columns(3)

    with col1:

        admin_name = st.text_input(
            "Product Name"
        )

    with col2:

        admin_price = st.number_input(
            "Price",
            min_value=0.0,
            step=0.01
        )

    with col3:

        admin_stock = st.number_input(
            "Stock",
            min_value=0,
            step=1
        )


    if st.button(
        "➕ Add Product",
        type="primary"
    ):

        response = requests.post(
            API_URL + "/products",
            headers=HEADERS,
            json={
                "name": admin_name,
                "price": admin_price,
                "stock": admin_stock
            }
        )

        if response.status_code == 200:

            st.success(
                "Product added successfully."
            )

            st.rerun()

        else:

            st.error(
                response.json()["detail"]
            )


    st.divider()


    # =====================================================
    # ADMIN ORDERS
    # =====================================================

    st.header("📦 Orders")

    response = requests.get(
        API_URL + "/orders",
        headers=HEADERS
    )

    if response.status_code == 200:

        orders = response.json()

        if len(orders) == 0:

            st.info(
                "No orders yet."
            )

        else:

            for order in orders:

                st.write(
                    f"**Order #{order['id']}** | "
                    f"Customer: {order['username']} | "
                    f"Total: ₹{order['total']:.2f} | "
                    f"Status: {order['status']} | "
                    f"{order['created_at']}"
                )


# =========================================================
# GET ALL PRODUCTS
# =========================================================

response = requests.get(
    API_URL + "/products",
    headers=HEADERS
)

if response.status_code != 200:

    st.error(
        "Unable to load products."
    )

    st.stop()

products = response.json()


# =========================================================
# USER SHOP
# =========================================================

if st.session_state.role == "user":

    st.title("🛍️ Online Store")

    st.subheader(
        "Choose products and quantities"
    )


    # =====================================================
    # SEARCH
    # =====================================================

    search_text = st.text_input(
        "🔍 Search products"
    )

    if search_text.strip():

        response = requests.get(
            API_URL
            + "/products/search/"
            + search_text.strip(),
            headers=HEADERS
        )

        if response.status_code == 200:

            products = response.json()


    # =====================================================
    # PRODUCTS
    # =====================================================

    for product in products:

        col1, col2, col3, col4 = st.columns(
            [3, 2, 2, 1.5]
        )

        with col1:

            st.subheader(
                product["name"]
            )

        with col2:

            st.write(
                "₹" + f"{product['price']:.2f}"
            )

        with col3:

            if product["stock"] == 0:

                st.error(
                    "Out of stock"
                )

            else:

                st.write(
                    "Available:",
                    product["stock"]
                )

        with col4:

            if product["stock"] > 0:

                quantity = st.number_input(
                    "Qty",
                    min_value=0,
                    max_value=product["stock"],
                    step=1,
                    key="quantity_" + str(product["id"])
                )

                if st.button(
                    "🛒 Add",
                    key="cart_" + str(product["id"])
                ):

                    current_quantity = (
                        st.session_state.cart.get(
                            product["id"],
                            0
                        )
                    )

                    new_quantity = (
                        current_quantity + quantity
                    )

                    if quantity <= 0:

                        st.warning(
                            "Select a quantity first."
                        )

                    elif new_quantity > product["stock"]:

                        st.error(
                            "You cannot add more than "
                            "available stock."
                        )

                    else:

                        st.session_state.cart[
                            product["id"]
                        ] = new_quantity

                        st.success(
                            "Added to cart."
                        )

        st.divider()


    # =====================================================
    # CART
    # =====================================================

    st.header("🛒 My Cart")

    # Always get the latest prices/stocks
    response = requests.get(
        API_URL + "/products",
        headers=HEADERS
    )

    latest_products = response.json()

    product_lookup = {}

    for product in latest_products:

        product_lookup[
            product["id"]
        ] = product


    cart_rows = []
    cart_total = 0.0


    for product_id, quantity in list(
        st.session_state.cart.items()
    ):

        product = product_lookup.get(
            product_id
        )

        if product is None:

            del st.session_state.cart[
                product_id
            ]

            continue


        # If stock changed lower, reduce cart quantity
        if quantity > product["stock"]:

            quantity = product["stock"]

            if quantity == 0:

                del st.session_state.cart[
                    product_id
                ]

                continue

            st.session_state.cart[
                product_id
            ] = quantity


        item_total = (
            product["price"] * quantity
        )

        cart_total += item_total

        cart_rows.append({
            "id": product_id,
            "name": product["name"],
            "price": product["price"],
            "quantity": quantity,
            "total": item_total
        })


    if len(cart_rows) == 0:

        st.info(
            "Your cart is empty."
        )

    else:

        for item in cart_rows:

            col1, col2, col3, col4 = st.columns(
                [3, 2, 1, 2]
            )

            with col1:

                st.write(
                    "**" + item["name"] + "**"
                )

            with col2:

                st.write(
                    "₹" + f"{item['price']:.2f}"
                )

            with col3:

                st.write(
                    "Qty:",
                    item["quantity"]
                )

            with col4:

                st.write(
                    "Total: ₹"
                    + f"{item['total']:.2f}"
                )


        st.divider()

        st.subheader(
            "Cart Total: ₹"
            + f"{cart_total:.2f}"
        )


        # =================================================
        # CHECKOUT
        # =================================================

        if st.button(
            "💳 Checkout / Buy Now",
            type="primary",
            use_container_width=True
        ):

            checkout_items = []

            for item in cart_rows:

                checkout_items.append({
                    "product_id": item["id"],
                    "quantity": item["quantity"]
                })


            response = requests.post(
                API_URL + "/checkout",
                headers=HEADERS,
                json={
                    "items": checkout_items
                }
            )


            if response.status_code == 200:

                result = response.json()

                st.session_state.cart = {}

                st.success(
                    "✅ Order placed successfully!"
                )

                st.success(
                    "Order ID: "
                    + str(result["order_id"])
                )

                st.success(
                    "Amount: ₹"
                    + f"{result['total']:.2f}"
                )

                st.rerun()

            else:

                st.error(
                    response.json()["detail"]
                )


    # =====================================================
    # ORDER HISTORY
    # =====================================================

    st.divider()

    st.header("📜 My Orders")

    response = requests.get(
        API_URL + "/orders/me",
        headers=HEADERS
    )

    if response.status_code == 200:

        orders = response.json()

        if len(orders) == 0:

            st.info(
                "No orders yet."
            )

        else:

            for order in orders:

                st.write(
                    f"Order #{order['id']} | "
                    f"₹{order['total']:.2f} | "
                    f"{order['status']} | "
                    f"{order['created_at']}"
                )


# =========================================================
# ADMIN PRODUCT MANAGEMENT
# =========================================================

if st.session_state.role == "admin":

    st.header("📦 Product Management")


    if len(products) == 0:

        st.info(
            "No products available."
        )

    else:

        for product in products:

            col1, col2, col3, col4, col5 = st.columns(
                [3, 2, 1.5, 1, 1]
            )

            with col1:

                st.write(
                    "**" + product["name"] + "**"
                )

            with col2:

                st.write(
                    "₹" + f"{product['price']:.2f}"
                )

            with col3:

                st.write(
                    "Stock:",
                    product["stock"]
                )

            with col4:

                if st.button(
                    "✏️ Update",
                    key="update_" + str(product["id"])
                ):

                    st.session_state.edit_id = (
                        product["id"]
                    )

                    st.rerun()

            with col5:

                if st.button(
                    "🗑️ Delete",
                    key="delete_" + str(product["id"])
                ):

                    response = requests.delete(
                        API_URL
                        + "/products/"
                        + str(product["id"]),
                        headers=HEADERS
                    )

                    if response.status_code == 200:

                        st.success(
                            "Product deleted."
                        )

                        st.rerun()

                    else:

                        st.error(
                            response.json()["detail"]
                        )


    # =====================================================
    # UPDATE PRODUCT
    # =====================================================

    if st.session_state.edit_id is not None:

        st.divider()

        st.header("✏️ Update Product")

        edit_id = st.session_state.edit_id

        selected_product = None

        for product in products:

            if product["id"] == edit_id:

                selected_product = product
                break


        if selected_product is not None:

            new_name = st.text_input(
                "New Product Name",
                value=selected_product["name"],
                key="edit_name"
            )

            new_price = st.number_input(
                "New Price",
                min_value=0.0,
                value=float(
                    selected_product["price"]
                ),
                step=0.01,
                key="edit_price"
            )

            new_stock = st.number_input(
                "New Stock",
                min_value=0,
                value=int(
                    selected_product["stock"]
                ),
                step=1,
                key="edit_stock"
            )


            col1, col2 = st.columns(2)


            with col1:

                if st.button(
                    "💾 Save Changes",
                    type="primary",
                    use_container_width=True
                ):

                    response = requests.put(
                        API_URL
                        + "/products/"
                        + str(edit_id),
                        headers=HEADERS,
                        json={
                            "name": new_name,
                            "price": new_price,
                            "stock": new_stock
                        }
                    )

                    if response.status_code == 200:

                        st.session_state.edit_id = None

                        st.success(
                            "Product updated."
                        )

                        st.rerun()

                    else:

                        st.error(
                            response.json()["detail"]
                        )


            with col2:

                if st.button(
                    "❌ Cancel",
                    use_container_width=True
                ):

                    st.session_state.edit_id = None

                    st.rerun()
