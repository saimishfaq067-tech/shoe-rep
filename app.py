import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import random
import io

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="ShoeShop POS",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>
    .main {
        background-color: #f6f7fb;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    .pos-title {
        font-size: 34px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 0;
    }

    .pos-subtitle {
        color: #6b7280;
        margin-top: 0;
    }

    .stat-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 3px 15px rgba(0,0,0,0.06);
        border: 1px solid #e5e7eb;
    }

    .stat-label {
        color: #6b7280;
        font-size: 14px;
    }

    .stat-value {
        color: #111827;
        font-size: 28px;
        font-weight: 800;
    }

    .product-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 15px;
        padding: 16px;
        margin-bottom: 10px;
    }

    .product-name {
        font-size: 17px;
        font-weight: 700;
        color: #111827;
    }

    .product-meta {
        color: #6b7280;
        font-size: 13px;
    }

    .price {
        font-size: 20px;
        font-weight: 800;
        color: #2563eb;
    }

    .stock-good {
        color: #059669;
        font-weight: 700;
    }

    .stock-low {
        color: #d97706;
        font-weight: 700;
    }

    .stock-out {
        color: #dc2626;
        font-weight: 700;
    }

    section[data-testid="stSidebar"] {
        background: #111827;
    }

    section[data-testid="stSidebar"] * {
        color: white;
    }

    div.stButton > button {
        border-radius: 9px;
        font-weight: 600;
    }

    .invoice-box {
        background: white;
        border-radius: 14px;
        padding: 25px;
        border: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# DATABASE
# =========================================================

DB_NAME = "shoe_shop_pos.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


conn = get_connection()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    brand TEXT NOT NULL,
    size TEXT NOT NULL,
    color TEXT NOT NULL,
    sku TEXT UNIQUE NOT NULL,
    price REAL NOT NULL,
    cost REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT UNIQUE NOT NULL,
    customer TEXT,
    subtotal REAL,
    discount REAL,
    tax REAL,
    total REAL,
    payment_method TEXT,
    seller TEXT,
    created_at TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT,
    product_id INTEGER,
    product_name TEXT,
    quantity INTEGER,
    price REAL,
    total REAL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

conn.commit()

# =========================================================
# SETTINGS
# =========================================================

def get_setting(key, default):
    row = cur.execute(
        "SELECT value FROM settings WHERE key=?",
        (key,)
    ).fetchone()

    if row:
        return row["value"]

    cur.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES (?,?)",
        (key, str(default))
    )
    conn.commit()
    return str(default)


def save_setting(key, value):
    cur.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES (?,?)",
        (key, str(value))
    )
    conn.commit()


STORE_NAME = get_setting("store_name", "ShoeShop")
CURRENCY = get_setting("currency", "PKR")

# =========================================================
# SAMPLE 100 PRODUCTS
# =========================================================

def generate_products():
    brands = [
        "Nike", "Adidas", "Puma", "Bata", "Servis",
        "Skechers", "Reebok", "Hush Puppies", "Clarks", "Metro"
    ]

    categories = [
        "Running", "Casual", "Formal", "Sports", "Sneakers",
        "Boots", "Sandals", "School", "Loafers", "Slippers"
    ]

    colors = [
        "Black", "White", "Blue", "Red", "Brown",
        "Grey", "Green", "Navy", "Beige", "Maroon"
    ]

    products = []

    counter = 1

    for brand in brands:
        for category in categories:

            if counter > 100:
                break

            name = f"{brand} {category} Pro {counter}"

            size = random.choice([
                "6,7,8,9,10",
                "7,8,9,10,11",
                "8,9,10,11,12"
            ])

            color = random.choice(colors)

            cost = random.randint(1800, 6500)
            price = cost + random.randint(700, 3000)

            products.append({
                "name": name,
                "category": category,
                "brand": brand,
                "size": size,
                "color": color,
                "sku": f"SHOE-{counter:04d}",
                "price": price,
                "cost": cost,
                "stock": random.randint(5, 40)
            })

            counter += 1

    return products


def seed_products():
    count = cur.execute(
        "SELECT COUNT(*) AS total FROM products"
    ).fetchone()["total"]

    if count == 0:
        products = generate_products()

        for p in products:
            cur.execute("""
                INSERT INTO products
                (name, category, brand, size, color, sku,
                 price, cost, stock, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["name"],
                p["category"],
                p["brand"],
                p["size"],
                p["color"],
                p["sku"],
                p["price"],
                p["cost"],
                p["stock"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

        conn.commit()


seed_products()

# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "last_invoice" not in st.session_state:
    st.session_state.last_invoice = None

# =========================================================
# LOGIN
# =========================================================

if not st.session_state.logged_in:

    st.markdown(
        "<h1 style='text-align:center;'>👟 ShoeShop POS</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center;color:#6b7280;'>Professional Shoe Store Management System</p>",
        unsafe_allow_html=True
    )

    st.write("")

    left, center, right = st.columns([1, 1.2, 1])

    with center:

        st.markdown("### 🔐 Login")

        login_type = st.selectbox(
            "Select User",
            ["Seller", "Admin"]
        )

        if login_type == "Admin":

            password = st.text_input(
                "Admin Password",
                type="password"
            )

            if st.button(
                "Login as Admin",
                use_container_width=True
            ):

                if password == "viki90":
                    st.session_state.logged_in = True
                    st.session_state.role = "Admin"
                    st.rerun()
                else:
                    st.error("Incorrect admin password.")

        else:

            seller_name = st.text_input(
                "Seller Name",
                value="Seller"
            )

            if st.button(
                "Enter POS",
                use_container_width=True
            ):

                st.session_state.logged_in = True
                st.session_state.role = seller_name.strip() or "Seller"
                st.rerun()

    st.stop()

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown(
    f"""
    <div style='text-align:center; padding:10px;'>
        <div style='font-size:45px;'>👟</div>
        <h2>{STORE_NAME}</h2>
        <p>POS SYSTEM</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.divider()

st.sidebar.write(
    f"👤 **User:** {st.session_state.role}"
)

menu = st.sidebar.radio(
    "MAIN MENU",
    [
        "📊 Dashboard",
        "🛒 New Sale",
        "📦 Inventory",
        "🧾 Sales History",
        "⚙️ Settings"
    ]
)

st.sidebar.divider()

if st.sidebar.button(
    "🚪 Logout",
    use_container_width=True
):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.cart = {}
    st.rerun()

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def money(value):
    return f"{CURRENCY} {value:,.0f}"


def get_products(search=""):
    if search.strip():

        term = f"%{search.strip()}%"

        return cur.execute("""
            SELECT * FROM products
            WHERE name LIKE ?
               OR category LIKE ?
               OR brand LIKE ?
               OR color LIKE ?
               OR size LIKE ?
               OR sku LIKE ?
            ORDER BY name
        """, (
            term, term, term, term, term, term
        )).fetchall()

    return cur.execute("""
        SELECT * FROM products
        ORDER BY id DESC
    """).fetchall()


def add_to_cart(product_id):

    product = cur.execute(
        "SELECT * FROM products WHERE id=?",
        (product_id,)
    ).fetchone()

    if not product:
        return

    current_qty = st.session_state.cart.get(product_id, 0)

    if current_qty >= product["stock"]:
        st.warning("Not enough stock available.")
        return

    st.session_state.cart[product_id] = current_qty + 1


def remove_from_cart(product_id):

    if product_id in st.session_state.cart:

        if st.session_state.cart[product_id] <= 1:
            del st.session_state.cart[product_id]
        else:
            st.session_state.cart[product_id] -= 1


def generate_invoice():
    return "INV-" + datetime.now().strftime("%Y%m%d%H%M%S")


# =========================================================
# DASHBOARD
# =========================================================

if menu == "📊 Dashboard":

    st.markdown(
        "<div class='pos-title'>Dashboard</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='pos-subtitle'>Shoe shop overview and business performance</div>",
        unsafe_allow_html=True
    )

    st.write("")

    total_products = cur.execute(
        "SELECT COUNT(*) AS c FROM products"
    ).fetchone()["c"]

    total_stock = cur.execute(
        "SELECT COALESCE(SUM(stock),0) AS c FROM products"
    ).fetchone()["c"]

    today = datetime.now().strftime("%Y-%m-%d")

    today_sales = cur.execute("""
        SELECT
            COUNT(*) AS count,
            COALESCE(SUM(total),0) AS total
        FROM sales
        WHERE DATE(created_at)=?
    """, (today,)).fetchone()

    inventory_value = cur.execute("""
        SELECT COALESCE(SUM(stock * cost),0) AS value
        FROM products
    """).fetchone()["value"]

    low_stock = cur.execute("""
        SELECT COUNT(*) AS c
        FROM products
        WHERE stock <= 5
    """).fetchone()["c"]

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown(
            f"""
            <div class='stat-card'>
                <div class='stat-label'>Today's Sales</div>
                <div class='stat-value'>{money(today_sales["total"])}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class='stat-card'>
                <div class='stat-label'>Transactions</div>
                <div class='stat-value'>{today_sales["count"]}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f"""
            <div class='stat-card'>
                <div class='stat-label'>Products</div>
                <div class='stat-value'>{total_products}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            f"""
            <div class='stat-card'>
                <div class='stat-label'>Stock Units</div>
                <div class='stat-value'>{total_stock}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c5:
        st.markdown(
            f"""
            <div class='stat-card'>
                <div class='stat-label'>Low Stock</div>
                <div class='stat-value'>{low_stock}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("📦 Low Stock Products")

        low_products = cur.execute("""
            SELECT name, brand, stock, price
            FROM products
            WHERE stock <= 5
            ORDER BY stock ASC
            LIMIT 10
        """).fetchall()

        if low_products:

            df = pd.DataFrame(
                [dict(x) for x in low_products]
            )

            df.columns = [
                "Product",
                "Brand",
                "Stock",
                "Price"
            ]

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.success("All products have healthy stock.")

    with col2:

        st.subheader("🧾 Recent Sales")

        recent_sales = cur.execute("""
            SELECT invoice_no, customer, total,
                   payment_method, created_at
            FROM sales
            ORDER BY id DESC
            LIMIT 10
        """).fetchall()

        if recent_sales:

            df = pd.DataFrame(
                [dict(x) for x in recent_sales]
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No sales recorded yet.")

    st.divider()

    st.subheader("📊 Inventory Value")

    st.metric(
        "Current Inventory Cost Value",
        money(inventory_value)
    )

# =========================================================
# NEW SALE
# =========================================================

elif menu == "🛒 New Sale":

    st.markdown(
        "<div class='pos-title'>New Sale</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='pos-subtitle'>Search products and create customer invoices</div>",
        unsafe_allow_html=True
    )

    st.write("")

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    search = st.text_input(
        "🔎 Search Product",
        placeholder="Search by name, brand, category, color, size or SKU..."
    )

    products = get_products(search)

    st.caption(
        f"{len(products)} product(s) found"
    )

    # -----------------------------------------------------
    # PRODUCTS
    # -----------------------------------------------------

    left, right = st.columns([1.8, 1])

    with left:

        if not products:

            st.warning("No matching products found.")

        else:

            for product in products[:50]:

                col1, col2, col3, col4 = st.columns(
                    [3, 1.2, 1.2, 0.9]
                )

                with col1:

                    st.markdown(
                        f"""
                        <div class='product-card'>
                            <div class='product-name'>
                                👟 {product["name"]}
                            </div>
                            <div class='product-meta'>
                                {product["brand"]} •
                                {product["category"]} •
                                {product["color"]}
                            </div>
                            <div class='product-meta'>
                                SKU: {product["sku"]} |
                                Sizes: {product["size"]}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:
                    st.markdown(
                        f"### {money(product['price'])}"
                    )

                with col3:

                    if product["stock"] <= 0:
                        st.markdown(
                            "<span class='stock-out'>OUT OF STOCK</span>",
                            unsafe_allow_html=True
                        )
                    elif product["stock"] <= 5:
                        st.markdown(
                            f"<span class='stock-low'>Stock: {product['stock']}</span>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"<span class='stock-good'>Stock: {product['stock']}</span>",
                            unsafe_allow_html=True
                        )

                with col4:

                    if product["stock"] > 0:

                        if st.button(
                            "Add",
                            key=f"add_{product['id']}"
                        ):
                            add_to_cart(product["id"])
                            st.rerun()

                st.divider()

    # -----------------------------------------------------
    # CART
    # -----------------------------------------------------

    with right:

        st.subheader("🛒 Current Cart")

        if not st.session_state.cart:

            st.info("Cart is empty.")

        else:

            subtotal = 0

            for product_id, quantity in list(
                st.session_state.cart.items()
            ):

                product = cur.execute(
                    "SELECT * FROM products WHERE id=?",
                    (product_id,)
                ).fetchone()

                if not product:
                    continue

                item_total = product["price"] * quantity
                subtotal += item_total

                st.markdown(
                    f"""
                    **{product["name"]}**

                    {quantity} × {money(product["price"])}
                    
                    **{money(item_total)}**
                    """
                )

                c1, c2, c3 = st.columns(3)

                with c1:
                    if st.button(
                        "−",
                        key=f"minus_{product_id}"
                    ):
                        remove_from_cart(product_id)
                        st.rerun()

                with c2:
                    st.write(f"Qty: {quantity}")

                with c3:
                    if st.button(
                        "＋",
                        key=f"plus_{product_id}"
                    ):
                        add_to_cart(product_id)
                        st.rerun()

                st.divider()

            discount = st.number_input(
                "Discount",
                min_value=0.0,
                value=0.0,
                step=100.0
            )

            tax_percent = st.number_input(
                "Tax %",
                min_value=0.0,
                value=0.0,
                step=1.0
            )

            customer = st.text_input(
                "Customer Name",
                value="Walk-in Customer"
            )

            payment = st.selectbox(
                "Payment Method",
                [
                    "Cash",
                    "Card",
                    "Bank Transfer",
                    "JazzCash",
                    "EasyPaisa"
                ]
            )

            taxable = max(subtotal - discount, 0)
            tax = taxable * tax_percent / 100
            total = taxable + tax

            st.divider()

            st.markdown(
                f"""
                **Subtotal:** {money(subtotal)}

                **Discount:** {money(discount)}

                **Tax:** {money(tax)}

                # Total: {money(total)}
                """
            )

            if st.button(
                "💳 COMPLETE SALE",
                use_container_width=True,
                type="primary"
            ):

                invoice_no = generate_invoice()
                now = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                # Save sale
                cur.execute("""
                    INSERT INTO sales
                    (invoice_no, customer, subtotal, discount,
                     tax, total, payment_method, seller, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    invoice_no,
                    customer,
                    subtotal,
                    discount,
                    tax,
                    total,
                    payment,
                    st.session_state.role,
                    now
                ))

                # Save items and reduce inventory
                for product_id, quantity in st.session_state.cart.items():

                    product = cur.execute(
                        "SELECT * FROM products WHERE id=?",
                        (product_id,)
                    ).fetchone()

                    if product["stock"] < quantity:

                        st.error(
                            f"Insufficient stock for {product['name']}"
                        )
                        conn.rollback()
                        st.stop()

                    item_total = product["price"] * quantity

                    cur.execute("""
                        INSERT INTO sale_items
                        (invoice_no, product_id, product_name,
                         quantity, price, total)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        invoice_no,
                        product_id,
                        product["name"],
                        quantity,
                        product["price"],
                        item_total
                    ))

                    cur.execute("""
                        UPDATE products
                        SET stock = stock - ?
                        WHERE id=?
                    """, (
                        quantity,
                        product_id
                    ))

                conn.commit()

                st.session_state.last_invoice = invoice_no
                st.session_state.cart = {}

                st.success(
                    f"Sale completed successfully! Invoice: {invoice_no}"
                )

                st.rerun()

# =========================================================
# INVENTORY
# =========================================================

elif menu == "📦 Inventory":

    st.markdown(
        "<div class='pos-title'>Inventory Management</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='pos-subtitle'>Manage products, pricing and stock</div>",
        unsafe_allow_html=True
    )

    st.write("")

    if st.session_state.role != "Admin":

        st.info(
            "Inventory management is available to Admin only."
        )

    else:

        tabs = st.tabs([
            "📋 Products",
            "➕ Add Product",
            "✏️ Edit Product",
            "🗑️ Delete Product"
        ])

        # -------------------------------------------------
        # PRODUCTS
        # -------------------------------------------------

        with tabs[0]:

            search_inventory = st.text_input(
                "🔎 Search Inventory",
                placeholder="Search product..."
            )

            rows = get_products(search_inventory)

            df = pd.DataFrame(
                [dict(x) for x in rows]
            )

            if not df.empty:

                display_columns = [
                    "id",
                    "name",
                    "brand",
                    "category",
                    "size",
                    "color",
                    "sku",
                    "price",
                    "stock"
                ]

                df = df[display_columns]

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                csv = df.to_csv(index=False).encode("utf-8")

                st.download_button(
                    "⬇️ Export Inventory CSV",
                    data=csv,
                    file_name="shoe_inventory.csv",
                    mime="text/csv"
                )

        # -------------------------------------------------
        # ADD
        # -------------------------------------------------

        with tabs[1]:

            st.subheader("Add New Product")

            with st.form("add_product"):

                name = st.text_input("Product Name")
                brand = st.text_input("Brand")
                category = st.selectbox(
                    "Category",
                    [
                        "Running",
                        "Casual",
                        "Formal",
                        "Sports",
                        "Sneakers",
                        "Boots",
                        "Sandals",
                        "School",
                        "Loafers",
                        "Slippers"
                    ]
                )

                size = st.text_input(
                    "Sizes",
                    value="6,7,8,9,10"
                )

                color = st.text_input(
                    "Color",
                    value="Black"
                )

                sku = st.text_input(
                    "SKU / Barcode",
                    value=f"SHOE-{random.randint(10000,99999)}"
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    cost = st.number_input(
                        "Cost Price",
                        min_value=0.0,
                        step=100.0
                    )

                with col2:
                    price = st.number_input(
                        "Sale Price",
                        min_value=0.0,
                        step=100.0
                    )

                with col3:
                    stock = st.number_input(
                        "Opening Stock",
                        min_value=0,
                        step=1
                    )

                submitted = st.form_submit_button(
                    "Add Product",
                    type="primary"
                )

                if submitted:

                    if not name or not brand or not sku:

                        st.error(
                            "Name, Brand and SKU are required."
                        )

                    else:

                        try:

                            cur.execute("""
                                INSERT INTO products
                                (name, category, brand, size,
                                 color, sku, price, cost,
                                 stock, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                name,
                                category,
                                brand,
                                size,
                                color,
                                sku,
                                price,
                                cost,
                                stock,
                                datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )
                            ))

                            conn.commit()

                            st.success(
                                "Product added successfully."
                            )

                        except sqlite3.IntegrityError:

                            st.error(
                                "This SKU already exists."
                            )

        # -------------------------------------------------
        # EDIT
        # -------------------------------------------------

        with tabs[2]:

            products_all = cur.execute(
                "SELECT * FROM products ORDER BY name"
            ).fetchall()

            if products_all:

                product_options = {
                    f"{p['name']} | {p['sku']}": p["id"]
                    for p in products_all
                }

                selected_label = st.selectbox(
                    "Select Product",
                    list(product_options.keys())
                )

                selected_id = product_options[selected_label]

                product = cur.execute(
                    "SELECT * FROM products WHERE id=?",
                    (selected_id,)
                ).fetchone()

                with st.form("edit_product"):

                    new_name = st.text_input(
                        "Product Name",
                        value=product["name"]
                    )

                    new_brand = st.text_input(
                        "Brand",
                        value=product["brand"]
                    )

                    new_category = st.text_input(
                        "Category",
                        value=product["category"]
                    )

                    new_size = st.text_input(
                        "Sizes",
                        value=product["size"]
                    )

                    new_color = st.text_input(
                        "Color",
                        value=product["color"]
                    )

                    new_price = st.number_input(
                        "Sale Price",
                        min_value=0.0,
                        value=float(product["price"]),
                        step=100.0
                    )

                    new_cost = st.number_input(
                        "Cost Price",
                        min_value=0.0,
                        value=float(product["cost"]),
                        step=100.0
                    )

                    new_stock = st.number_input(
                        "Stock",
                        min_value=0,
                        value=int(product["stock"]),
                        step=1
                    )

                    update = st.form_submit_button(
                        "Save Changes",
                        type="primary"
                    )

                    if update:

                        cur.execute("""
                            UPDATE products
                            SET name=?,
                                brand=?,
                                category=?,
                                size=?,
                                color=?,
                                price=?,
                                cost=?,
                                stock=?
                            WHERE id=?
                        """, (
                            new_name,
                            new_brand,
                            new_category,
                            new_size,
                            new_color,
                            new_price,
                            new_cost,
                            new_stock,
                            selected_id
                        ))

                        conn.commit()

                        st.success(
                            "Product updated successfully."
                        )

        # -------------------------------------------------
        # DELETE
        # -------------------------------------------------

        with tabs[3]:

            products_all = cur.execute(
                "SELECT * FROM products ORDER BY name"
            ).fetchall()

            if products_all:

                product_options = {
                    f"{p['name']} | {p['sku']}": p["id"]
                    for p in products_all
                }

                selected_label = st.selectbox(
                    "Product to Delete",
                    list(product_options.keys()),
                    key="delete_product"
                )

                selected_id = product_options[selected_label]

                st.warning(
                    "Deleting a product cannot be undone."
                )

                confirm = st.checkbox(
                    "I understand and want to delete this product."
                )

                if st.button(
                    "🗑️ Delete Product",
                    disabled=not confirm
                ):

                    cur.execute(
                        "DELETE FROM products WHERE id=?",
                        (selected_id,)
                    )

                    conn.commit()

                    st.success(
                        "Product deleted."
                    )

                    st.rerun()

# =========================================================
# SALES HISTORY
# =========================================================

elif menu == "🧾 Sales History":

    st.markdown(
        "<div class='pos-title'>Sales History</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='pos-subtitle'>View completed transactions</div>",
        unsafe_allow_html=True
    )

    st.write("")

    rows = cur.execute("""
        SELECT invoice_no,
               customer,
               subtotal,
               discount,
               tax,
               total,
               payment_method,
               seller,
               created_at
        FROM sales
        ORDER BY id DESC
    """).fetchall()

    if rows:

        df = pd.DataFrame(
            [dict(x) for x in rows]
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Download Sales CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="sales_history.csv",
            mime="text/csv"
        )

        st.divider()

        st.subheader("🔍 Invoice Details")

        invoices = [x["invoice_no"] for x in rows]

        invoice = st.selectbox(
            "Select Invoice",
            invoices
        )

        invoice_items = cur.execute("""
            SELECT product_name,
                   quantity,
                   price,
                   total
            FROM sale_items
            WHERE invoice_no=?
        """, (invoice,)).fetchall()

        if invoice_items:

            item_df = pd.DataFrame(
                [dict(x) for x in invoice_items]
            )

            st.dataframe(
                item_df,
                use_container_width=True,
                hide_index=True
            )

    else:

        st.info("No sales available.")

# =========================================================
# SETTINGS
# =========================================================

elif menu == "⚙️ Settings":

    st.markdown(
        "<div class='pos-title'>Settings</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='pos-subtitle'>Manage your POS configuration</div>",
        unsafe_allow_html=True
    )

    st.write("")

    if st.session_state.role != "Admin":

        st.warning(
            "Only Admin can access settings."
        )

    else:

        tab1, tab2, tab3 = st.tabs([
            "🏪 Store",
            "💰 Currency",
            "🔐 Security"
        ])

        with tab1:

            st.subheader("Store Settings")

            new_store_name = st.text_input(
                "Store Name",
                value=STORE_NAME
            )

            if st.button("Save Store Settings"):

                save_setting(
                    "store_name",
                    new_store_name
                )

                st.success(
                    "Store settings saved. Refresh the page."
                )

        with tab2:

            st.subheader("Currency")

            new_currency = st.selectbox(
                "Currency",
                ["PKR", "USD", "EUR", "GBP", "AED", "SAR"],
                index=[
                    "PKR",
                    "USD",
                    "EUR",
                    "GBP",
                    "AED",
                    "SAR"
                ].index(CURRENCY)
            )

            if st.button("Save Currency"):

                save_setting(
                    "currency",
                    new_currency
                )

                st.success(
                    "Currency saved. Refresh the page."
                )

        with tab3:

            st.subheader("Admin Security")

            st.info(
                "Current admin password is configured in the application code."
            )

            st.write(
                "Admin login password: `viki90`"
            )

            st.warning(
                "For a real production system, the password should be stored securely instead of directly inside source code."
            )

# =========================================================
# FOOTER
# =========================================================

st.sidebar.markdown(
    """
    <div style='position:fixed; bottom:10px; font-size:12px;'>
        ShoeShop POS • Professional Edition
    </div>
    """,
    unsafe_allow_html=True
)
