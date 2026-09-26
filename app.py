import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ============================================================
# APP CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Shoe Shop POS",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "shoe_shop_pos.db"
ADMIN_PASSWORD = "viki90"


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown("""
<style>

body {
    font-family: Arial, sans-serif;
}

.stApp {
    background: #f4f6f9;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #172033;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {
    color: white !important;
}

/* Main heading */
.page-title {
    font-size: 36px;
    font-weight: 800;
    color: #172033;
    margin-bottom: 5px;
}

.page-subtitle {
    font-size: 16px;
    color: #667085;
    margin-bottom: 25px;
}

/* Cards */
.card {
    background: white;
    border: 1px solid #e4e7ec;
    border-radius: 15px;
    padding: 22px;
    margin-bottom: 18px;
}

.card-title {
    font-size: 21px;
    font-weight: 800;
    color: #172033;
    margin-bottom: 15px;
}

/* Metric */
.metric {
    background: white;
    border: 1px solid #e4e7ec;
    border-radius: 15px;
    padding: 20px;
    min-height: 125px;
}

.metric-label {
    font-size: 14px;
    color: #667085;
    font-weight: 700;
}

.metric-number {
    font-size: 30px;
    color: #172033;
    font-weight: 800;
    margin-top: 10px;
}

/* Product */
.product-box {
    background: white;
    border: 1px solid #dfe3e8;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 12px;
}

.product-title {
    font-size: 18px;
    font-weight: 800;
    color: #172033;
}

.product-details {
    font-size: 13px;
    color: #667085;
    margin-top: 6px;
}

.product-price {
    font-size: 21px;
    font-weight: 800;
    color: #111827;
}

.stock-number {
    font-size: 16px;
    font-weight: 800;
}

/* Cart */
.cart-box {
    background: white;
    border: 2px solid #dfe3e8;
    border-radius: 15px;
    padding: 20px;
}

/* Role */
.admin-badge {
    background: #2563eb;
    color: white;
    padding: 8px 14px;
    border-radius: 20px;
    text-align: center;
    font-weight: 800;
    margin-bottom: 12px;
}

.seller-badge {
    background: #059669;
    color: white;
    padding: 8px 14px;
    border-radius: 20px;
    text-align: center;
    font-weight: 800;
    margin-bottom: 12px;
}

/* Buttons */
.stButton > button {
    border-radius: 9px;
    font-weight: 700;
}

/* Login */
.login-box {
    background: white;
    border: 1px solid #e4e7ec;
    border-radius: 18px;
    padding: 30px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.07);
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def connect_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# DATABASE SETUP
# ============================================================

def setup_database():

    conn = connect_db()
    cur = conn.cursor()

    # --------------------------------------------------------
    # PRODUCTS TABLE
    # --------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT DEFAULT '',
            brand TEXT DEFAULT '',
            color TEXT DEFAULT '',
            size TEXT DEFAULT '',
            price REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 5,
            created_at TEXT
        )
    """)

    # --------------------------------------------------------
    # DATABASE MIGRATION
    # --------------------------------------------------------

    columns = [
        row["name"]
        for row in cur.execute(
            "PRAGMA table_info(products)"
        ).fetchall()
    ]

    required_columns = {
        "category": "TEXT DEFAULT ''",
        "brand": "TEXT DEFAULT ''",
        "color": "TEXT DEFAULT ''",
        "size": "TEXT DEFAULT ''",
        "price": "REAL DEFAULT 0",
        "stock": "INTEGER DEFAULT 0",
        "min_stock": "INTEGER DEFAULT 5",
        "created_at": "TEXT"
    }

    for column, definition in required_columns.items():

        if column not in columns:

            cur.execute(
                f"""
                ALTER TABLE products
                ADD COLUMN {column} {definition}
                """
            )

    cur.execute("""
        UPDATE products
        SET min_stock = 5
        WHERE min_stock IS NULL
    """)

    # --------------------------------------------------------
    # SALES TABLE
    # --------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE NOT NULL,
            seller TEXT,
            subtotal REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            total REAL DEFAULT 0,
            payment_method TEXT,
            created_at TEXT
        )
    """)

    # --------------------------------------------------------
    # SALE ITEMS
    # --------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            sku TEXT,
            quantity INTEGER,
            price REAL,
            total REAL
        )
    """)

    # --------------------------------------------------------
    # STOCK HISTORY
    # --------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            sku TEXT,
            product_name TEXT,
            quantity INTEGER,
            action TEXT,
            reason TEXT,
            created_by TEXT,
            created_at TEXT
        )
    """)

    # --------------------------------------------------------
    # SETTINGS
    # --------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cur.execute("""
        INSERT OR IGNORE INTO settings
        (key, value)
        VALUES ('store_name', 'Shoe Shop POS')
    """)

    cur.execute("""
        INSERT OR IGNORE INTO settings
        (key, value)
        VALUES ('currency', 'PKR')
    """)

    conn.commit()

    # --------------------------------------------------------
    # CREATE 100 PRODUCTS
    # --------------------------------------------------------

    count = cur.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if count == 0:

        brands = [
            "Nike",
            "Adidas",
            "Puma",
            "Bata",
            "Servis",
            "Skechers",
            "Reebok",
            "Clarks",
            "Power",
            "Urban Walk"
        ]

        categories = [
            "Sports",
            "Running",
            "Casual",
            "Formal",
            "Sneakers",
            "Sandals",
            "Boots",
            "School",
            "Kids",
            "Ladies"
        ]

        colors = [
            "Black",
            "White",
            "Blue",
            "Brown",
            "Grey",
            "Red",
            "Green"
        ]

        sizes = [
            "6",
            "7",
            "8",
            "9",
            "10",
            "11"
        ]

        for i in range(1, 101):

            brand = brands[(i - 1) % len(brands)]
            category = categories[(i - 1) % len(categories)]
            color = colors[(i - 1) % len(colors)]
            size = sizes[(i - 1) % len(sizes)]

            sku = f"SHOE-{i:04d}"
            name = f"{brand} {category} Shoe {i}"

            price = 2500 + ((i * 350) % 7500)
            stock = 10 + (i % 25)

            cur.execute("""
                INSERT INTO products
                (
                    sku,
                    name,
                    category,
                    brand,
                    color,
                    size,
                    price,
                    stock,
                    min_stock,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sku,
                name,
                category,
                brand,
                color,
                size,
                price,
                stock,
                5,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ))

    conn.commit()
    conn.close()


setup_database()


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "cart" not in st.session_state:
    st.session_state.cart = []


# ============================================================
# SETTINGS FUNCTIONS
# ============================================================

def get_setting(key, default=""):

    conn = connect_db()

    row = conn.execute(
        "SELECT value FROM settings WHERE key=?",
        (key,)
    ).fetchone()

    conn.close()

    if row:
        return row["value"]

    return default


def save_setting(key, value):

    conn = connect_db()

    conn.execute("""
        INSERT INTO settings
        (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value=excluded.value
    """, (
        key,
        value
    ))

    conn.commit()
    conn.close()


# ============================================================
# PRODUCT FUNCTIONS
# ============================================================

def all_products():

    conn = connect_db()

    df = pd.read_sql_query("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """, conn)

    conn.close()

    return df


def find_product(product_id):

    conn = connect_db()

    product = conn.execute("""
        SELECT *
        FROM products
        WHERE id=?
    """, (
        product_id,
    )).fetchone()

    conn.close()

    return product


def search_product(text):

    conn = connect_db()

    if not text.strip():

        df = pd.read_sql_query("""
            SELECT *
            FROM products
            ORDER BY name
        """, conn)

    else:

        value = "%" + text.strip() + "%"

        df = pd.read_sql_query("""
            SELECT *
            FROM products
            WHERE
                name LIKE ?
                OR sku LIKE ?
                OR brand LIKE ?
                OR category LIKE ?
                OR color LIKE ?
                OR size LIKE ?
            ORDER BY name
        """, conn, params=(
            value,
            value,
            value,
            value,
            value,
            value
        ))

    conn.close()

    return df


# ============================================================
# LOGIN
# ============================================================

def show_login():

    st.markdown(
        "<div style='text-align:center;font-size:70px;'>👟</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <h1 style="
        text-align:center;
        color:#172033;
        ">
        Shoe Shop POS
        </h1>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style="
        text-align:center;
        color:#667085;
        font-size:17px;
        ">
        Professional Point of Sale System
        </p>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    left, center, right = st.columns(
        [1, 1.2, 1]
    )

    with center:

        st.markdown(
            '<div class="login-box">',
            unsafe_allow_html=True
        )

        st.subheader("🔐 Login")

        login_type = st.radio(
            "Choose account",
            [
                "Seller",
                "Admin"
            ],
            horizontal=True
        )

        # ----------------------------------------------------
        # ADMIN LOGIN
        # ----------------------------------------------------

        if login_type == "Admin":

            password = st.text_input(
                "Admin Password",
                type="password"
            )

            if st.button(
                "🔐 Login as Admin",
                use_container_width=True,
                type="primary"
            ):

                if password == ADMIN_PASSWORD:

                    st.session_state.logged_in = True
                    st.session_state.role = "admin"
                    st.session_state.user_name = "Administrator"
                    st.session_state.cart = []

                    st.rerun()

                else:

                    st.error(
                        "Wrong admin password."
                    )

        # ----------------------------------------------------
        # SELLER LOGIN
        # ----------------------------------------------------

        else:

            seller_name = st.text_input(
                "Seller Name",
                placeholder="Enter seller name"
            )

            st.caption(
                "Seller does not need a password."
            )

            if st.button(
                "🛒 Login as Seller",
                use_container_width=True,
                type="primary"
            ):

                if seller_name.strip():

                    st.session_state.logged_in = True
                    st.session_state.role = "seller"
                    st.session_state.user_name = seller_name.strip()
                    st.session_state.cart = []

                    st.rerun()

                else:

                    st.warning(
                        "Please enter seller name."
                    )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

def admin_dashboard():

    if st.session_state.role != "admin":
        st.error("Access denied.")
        return

    st.markdown(
        "<div class='page-title'>📊 Admin Dashboard</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='page-subtitle'>
        Complete overview of your shoe shop
        </div>
        """,
        unsafe_allow_html=True
    )

    conn = connect_db()

    total_products = conn.execute("""
        SELECT COUNT(*)
        FROM products
    """).fetchone()[0]

    total_stock = conn.execute("""
        SELECT COALESCE(SUM(stock),0)
        FROM products
    """).fetchone()[0]

    low_stock = conn.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE stock <= COALESCE(min_stock,5)
    """).fetchone()[0]

    today_sales = conn.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM sales
        WHERE DATE(created_at)=DATE('now','localtime')
    """).fetchone()[0]

    total_sales = conn.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM sales
    """).fetchone()[0]

    total_orders = conn.execute("""
        SELECT COUNT(*)
        FROM sales
    """).fetchone()[0]

    conn.close()

    currency = get_setting(
        "currency",
        "PKR"
    )

    # --------------------------------------------------------
    # DASHBOARD CARDS
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-label">
                TOTAL PRODUCTS
                </div>
                <div class="metric-number">
                {total_products}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:

        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-label">
                TOTAL STOCK
                </div>
                <div class="metric-number">
                {total_stock}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:

        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-label">
                LOW STOCK
                </div>
                <div class="metric-number">
                {low_stock}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:

        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-label">
                TODAY SALES
                </div>
                <div class="metric-number">
                {today_sales:,.0f}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")

    # --------------------------------------------------------
    # SALES SUMMARY
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="card-title">💰 Sales Summary</div>',
            unsafe_allow_html=True
        )

        st.metric(
            "Total Sales",
            f"{total_sales:,.0f} {currency}"
        )

        st.metric(
            "Total Orders",
            total_orders
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="card-title">⚠️ Stock Alert</div>',
            unsafe_allow_html=True
        )

        if low_stock > 0:

            st.warning(
                f"{low_stock} products are low in stock."
            )

        else:

            st.success(
                "All products have enough stock."
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # LOW STOCK
    # --------------------------------------------------------

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="card-title">📦 Low Stock Products</div>',
        unsafe_allow_html=True
    )

    products = all_products()

    low_products = products[
        products["stock"]
        <= products["min_stock"].fillna(5)
    ]

    if low_products.empty:

        st.success(
            "No low-stock products."
        )

    else:

        st.dataframe(
            low_products[
                [
                    "sku",
                    "name",
                    "category",
                    "price",
                    "stock",
                    "min_stock"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# ADMIN INVENTORY
# ============================================================

def admin_inventory():

    if st.session_state.role != "admin":
        st.error("Access denied.")
        return

    st.markdown(
        "<div class='page-title'>📦 Inventory Management</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='page-subtitle'>
        Add products, add stock, edit products and manage inventory.
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_add, tab_stock, tab_manage = st.tabs([
        "➕ ADD PRODUCT",
        "📥 ADD STOCK",
        "✏️ MANAGE PRODUCTS"
    ])

    # ========================================================
    # ADD PRODUCT
    # ========================================================

    with tab_add:

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="card-title">➕ Add New Product</div>',
            unsafe_allow_html=True
        )

        with st.form("add_product"):

            c1, c2 = st.columns(2)

            with c1:

                name = st.text_input(
                    "Product Name *"
                )

                sku = st.text_input(
                    "SKU / Barcode *"
                )

                brand = st.text_input(
                    "Brand"
                )

                category = st.selectbox(
                    "Category",
                    [
                        "Sports",
                        "Running",
                        "Casual",
                        "Formal",
                        "Sneakers",
                        "Sandals",
                        "Boots",
                        "School",
                        "Kids",
                        "Ladies",
                        "Other"
                    ]
                )

            with c2:

                color = st.text_input(
                    "Color"
                )

                size = st.text_input(
                    "Size"
                )

                price = st.number_input(
                    "Selling Price",
                    min_value=0.0,
                    value=2500.0,
                    step=100.0
                )

                stock = st.number_input(
                    "Initial Stock",
                    min_value=0,
                    value=10,
                    step=1
                )

                min_stock = st.number_input(
                    "Low Stock Alert At",
                    min_value=0,
                    value=5,
                    step=1
                )

            submit = st.form_submit_button(
                "➕ ADD PRODUCT",
                type="primary",
                use_container_width=True
            )

            if submit:

                if not name.strip():

                    st.error(
                        "Product name is required."
                    )

                elif not sku.strip():

                    st.error(
                        "SKU is required."
                    )

                else:

                    conn = connect_db()

                    try:

                        cur = conn.execute("""
                            INSERT INTO products
                            (
                                sku,
                                name,
                                category,
                                brand,
                                color,
                                size,
                                price,
                                stock,
                                min_stock,
                                created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            sku.strip(),
                            name.strip(),
                            category,
                            brand.strip(),
                            color.strip(),
                            size.strip(),
                            price,
                            stock,
                            min_stock,
                            datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        ))

                        product_id = cur.lastrowid

                        if stock > 0:

                            conn.execute("""
                                INSERT INTO stock_history
                                (
                                    product_id,
                                    sku,
                                    product_name,
                                    quantity,
                                    action,
                                    reason,
                                    created_by,
                                    created_at
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                product_id,
                                sku.strip(),
                                name.strip(),
                                stock,
                                "INITIAL STOCK",
                                "New product",
                                st.session_state.user_name,
                                datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )
                            ))

                        conn.commit()
                        conn.close()

                        st.success(
                            "Product added successfully."
                        )

                    except sqlite3.IntegrityError:

                        conn.close()

                        st.error(
                            "This SKU already exists."
                        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    # ========================================================
    # ADD STOCK
    # ========================================================

    with tab_stock:

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="card-title">📥 Add Stock</div>',
            unsafe_allow_html=True
        )

        products = all_products()

        if products.empty:

            st.warning(
                "No products available."
            )

        else:

            options = {}

            for _, row in products.iterrows():

                options[
                    f"{row['sku']} | {row['name']} | Current Stock: {row['stock']}"
                ] = int(row["id"])

            selected = st.selectbox(
                "Select Product",
                list(options.keys())
            )

            product_id = options[selected]

            product = find_product(
                product_id
            )

            st.info(
                f"Product: {product['name']} | "
                f"SKU: {product['sku']} | "
                f"Current Stock: {product['stock']} | "
                f"Price: {product['price']:,.0f} "
                f"{get_setting('currency','PKR')}"
            )

            quantity = st.number_input(
                "Quantity to Add",
                min_value=1,
                value=1,
                step=1
            )

            reason = st.text_input(
                "Stock Reason",
                placeholder="Supplier delivery / New purchase"
            )

            if st.button(
                "📥 ADD STOCK",
                type="primary"
            ):

                if not reason.strip():

                    reason = "Stock added"

                conn = connect_db()

                new_stock = (
                    int(product["stock"])
                    + int(quantity)
                )

                conn.execute("""
                    UPDATE products
                    SET stock=?
                    WHERE id=?
                """, (
                    new_stock,
                    product_id
                ))

                conn.execute("""
                    INSERT INTO stock_history
                    (
                        product_id,
                        sku,
                        product_name,
                        quantity,
                        action,
                        reason,
                        created_by,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id,
                    product["sku"],
                    product["name"],
                    quantity,
                    "STOCK IN",
                    reason,
                    st.session_state.user_name,
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                ))

                conn.commit()
                conn.close()

                st.success(
                    f"Stock updated. New stock: {new_stock}"
                )

                st.rerun()

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    # ========================================================
    # MANAGE PRODUCTS
    # ========================================================

    with tab_manage:

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="card-title">📋 Product List</div>',
            unsafe_allow_html=True
        )

        search = st.text_input(
            "🔎 Search Products",
            placeholder="Name, SKU, brand, category, color or size"
        )

        products = search_product(
            search
        )

        st.dataframe(
            products[
                [
                    "id",
                    "sku",
                    "name",
                    "category",
                    "brand",
                    "color",
                    "size",
                    "price",
                    "stock",
                    "min_stock"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.markdown(
            "### ✏️ Edit Product"
        )

        if not products.empty:

            edit_options = {}

            for _, row in products.iterrows():

                edit_options[
                    f"{row['sku']} | {row['name']}"
                ] = int(row["id"])

            selected_edit = st.selectbox(
                "Choose Product",
                list(edit_options.keys())
            )

            edit_id = edit_options[
                selected_edit
            ]

            product = find_product(
                edit_id
            )

            with st.form("edit_product"):

                c1, c2 = st.columns(2)

                with c1:

                    edit_name = st.text_input(
                        "Product Name",
                        value=product["name"]
                    )

                    edit_sku = st.text_input(
                        "SKU",
                        value=product["sku"]
                    )

                    edit_brand = st.text_input(
                        "Brand",
                        value=product["brand"] or ""
                    )

                    edit_category = st.text_input(
                        "Category",
                        value=product["category"] or ""
                    )

                with c2:

                    edit_color = st.text_input(
                        "Color",
                        value=product["color"] or ""
                    )

                    edit_size = st.text_input(
                        "Size",
                        value=product["size"] or ""
                    )

                    edit_price = st.number_input(
                        "Selling Price",
                        min_value=0.0,
                        value=float(product["price"] or 0),
                        step=100.0
                    )

                    edit_min_stock = st.number_input(
                        "Low Stock Alert",
                        min_value=0,
                        value=int(product["min_stock"] or 5),
                        step=1
                    )

                save = st.form_submit_button(
                    "💾 SAVE PRODUCT",
                    type="primary",
                    use_container_width=True
                )

                if save:

                    conn = connect_db()

                    try:

                        conn.execute("""
                            UPDATE products
                            SET
                                name=?,
                                sku=?,
                                brand=?,
                                category=?,
                                color=?,
                                size=?,
                                price=?,
                                min_stock=?
                            WHERE id=?
                        """, (
                            edit_name.strip(),
                            edit_sku.strip(),
                            edit_brand.strip(),
                            edit_category.strip(),
                            edit_color.strip(),
                            edit_size.strip(),
                            edit_price,
                            edit_min_stock,
                            edit_id
                        ))

                        conn.commit()
                        conn.close()

                        st.success(
                            "Product updated successfully."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        conn.close()

                        st.error(
                            "That SKU already exists."
                        )

            st.markdown(
                "### 🗑️ Delete Product"
            )

            confirm = st.checkbox(
                "I understand this product will be permanently deleted."
            )

            if confirm:

                if st.button(
                    "🗑️ DELETE PRODUCT"
                ):

                    conn = connect_db()

                    conn.execute("""
                        DELETE FROM products
                        WHERE id=?
                    """, (
                        edit_id,
                    ))

                    conn.commit()
                    conn.close()

                    st.success(
                        "Product deleted."
                    )

                    st.rerun()

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )


# ============================================================
# SALES HISTORY
# ============================================================

def sales_history():

    if st.session_state.role != "admin":
        st.error("Access denied.")
        return

    st.markdown(
        "<div class='page-title'>🧾 Sales History</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='page-subtitle'>
        All sales completed by sellers.
        </div>
        """,
        unsafe_allow_html=True
    )

    conn = connect_db()

    sales = pd.read_sql_query("""
        SELECT
            invoice_no,
            seller,
            subtotal,
            discount,
            tax,
            total,
            payment_method,
            created_at
        FROM sales
        ORDER BY id DESC
    """, conn)

    conn.close()

    if sales.empty:

        st.info(
            "No sales have been completed yet."
        )

        return

    search = st.text_input(
        "🔎 Search Invoice / Seller"
    )

    if search:

        mask = (
            sales["invoice_no"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
            |
            sales["seller"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
        )

        sales = sales[mask]

    st.dataframe(
        sales,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# STOCK HISTORY
# ============================================================

def stock_history_page():

    if st.session_state.role != "admin":
        st.error("Access denied.")
        return

    st.markdown(
        "<div class='page-title'>📋 Stock History</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='page-subtitle'>
        Complete record of stock additions and sales deductions.
        </div>
        """,
        unsafe_allow_html=True
    )

    conn = connect_db()

    history = pd.read_sql_query("""
        SELECT
            sku,
            product_name,
            quantity,
            action,
            reason,
            created_by,
            created_at
        FROM stock_history
        ORDER BY id DESC
    """, conn)

    conn.close()

    if history.empty:

        st.info(
            "No stock history available."
        )

    else:

        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# SETTINGS
# ============================================================

def settings_page():

    if st.session_state.role != "admin":
        st.error("Access denied.")
        return

    st.markdown(
        "<div class='page-title'>⚙️ Settings</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='page-subtitle'>
        Configure your store.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True
    )

    store_name = st.text_input(
        "Store Name",
        value=get_setting(
            "store_name",
            "Shoe Shop POS"
        )
    )

    currency = st.text_input(
        "Currency",
        value=get_setting(
            "currency",
            "PKR"
        )
    )

    if st.button(
        "💾 SAVE SETTINGS",
        type="primary"
    ):

        save_setting(
            "store_name",
            store_name
        )

        save_setting(
            "currency",
            currency
        )

        st.success(
            "Settings saved successfully."
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# SELLER POS
# ============================================================

def seller_pos():

    if st.session_state.role != "seller":
        st.error("Access denied.")
        return

    st.markdown(
        "<div class='page-title'>🛒 New Sale</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class='page-subtitle'>
        Seller: <b>{st.session_state.user_name}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # PRODUCT SEARCH
    # ========================================================

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="card-title">🔎 Product Search</div>',
        unsafe_allow_html=True
    )

    search = st.text_input(
        "Search anything",
        placeholder=(
            "Type Nike, black, sports, 9, SHOE-0001 etc."
        )
    )

    products = search_product(
        search
    )

    st.write(
        f"Products found: **{len(products)}**"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    # ========================================================
    # PRODUCTS
    # ========================================================

    for _, product in products.head(50).iterrows():

        c1, c2, c3, c4 = st.columns(
            [4, 2, 1.5, 1]
        )

        with c1:

            st.markdown(
                f"""
                <div class="product-box">

                <div class="product-title">
                {product["name"]}
                </div>

                <div class="product-details">
                SKU: {product["sku"]}
                <br>
                Brand: {product["brand"]}
                |
                Category: {product["category"]}
                |
                Color: {product["color"]}
                |
                Size: {product["size"]}
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:

            st.markdown(
                f"""
                <div style="padding-top:22px;">

                <div style="
                color:#667085;
                font-size:12px;
                font-weight:700;
                ">
                SELLING PRICE
                </div>

                <div class="product-price">
                {product["price"]:,.0f}
                {get_setting("currency","PKR")}
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        with c3:

            if product["stock"] <= product["min_stock"]:

                st.markdown(
                    f"""
                    <div style="padding-top:22px;">

                    <div style="
                    color:#667085;
                    font-size:12px;
                    font-weight:700;
                    ">
                    AVAILABLE
                    </div>

                    <div style="
                    color:#dc2626;
                    font-size:17px;
                    font-weight:800;
                    ">
                    {product["stock"]} LEFT
                    </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    f"""
                    <div style="padding-top:22px;">

                    <div style="
                    color:#667085;
                    font-size:12px;
                    font-weight:700;
                    ">
                    AVAILABLE
                    </div>

                    <div style="
                    color:#059669;
                    font-size:17px;
                    font-weight:800;
                    ">
                    {product["stock"]} IN STOCK
                    </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with c4:

            st.write("")

            if product["stock"] > 0:

                if st.button(
                    "➕ ADD",
                    key=f"add_{product['id']}",
                    use_container_width=True
                ):

                    add_cart(
                        int(product["id"])
                    )

                    st.rerun()

            else:

                st.error(
                    "OUT"
                )

    # ========================================================
    # CART
    # ========================================================

    st.divider()

    st.markdown(
        "<div class='page-title' style='font-size:28px;'>🛍️ Shopping Cart</div>",
        unsafe_allow_html=True
    )

    if not st.session_state.cart:

        st.info(
            "Cart is empty. Add products above."
        )

        return

    subtotal = 0

    for index, item in enumerate(
        st.session_state.cart
    ):

        c1, c2, c3, c4, c5 = st.columns(
            [3.5, 1.5, 1.5, 1.5, 0.7]
        )

        with c1:

            st.write(
                f"**{item['name']}**"
            )

            st.caption(
                f"SKU: {item['sku']}"
            )

        with c2:

            st.write(
                f"Price: {item['price']:,.0f}"
            )

        with c3:

            quantity = st.number_input(
                "Quantity",
                min_value=1,
                max_value=max(
                    1,
                    item["stock"]
                ),
                value=item["quantity"],
                key=f"quantity_{index}"
            )

            st.session_state.cart[
                index
            ]["quantity"] = quantity

        with c4:

            item_total = (
                item["price"] *
                quantity
            )

            subtotal += item_total

            st.write(
                f"**{item_total:,.0f}**"
            )

        with c5:

            if st.button(
                "❌",
                key=f"remove_{index}"
            ):

                st.session_state.cart.pop(
                    index
                )

                st.rerun()

    # ========================================================
    # CHECKOUT
    # ========================================================

    st.divider()

    left, right = st.columns(
        [1, 1]
    )

    with left:

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="card-title">💳 Payment</div>',
            unsafe_allow_html=True
        )

        discount = st.number_input(
            "Discount",
            min_value=0.0,
            value=0.0,
            step=100.0
        )

        tax_percent = st.number_input(
            "Tax Percentage",
            min_value=0.0,
            value=0.0,
            step=1.0
        )

        payment = st.selectbox(
            "Payment Method",
            [
                "Cash",
                "Card",
                "Bank Transfer",
                "JazzCash",
                "Easypaisa"
            ]
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    with right:

        after_discount = max(
            0,
            subtotal - discount
        )

        tax = (
            after_discount *
            tax_percent /
            100
        )

        total = (
            after_discount +
            tax
        )

        currency = get_setting(
            "currency",
            "PKR"
        )

        st.markdown(
            f"""
            <div class="cart-box">

            <h2>🧾 Sale Summary</h2>

            <hr>

            <p>
            Subtotal:
            <b>{subtotal:,.2f} {currency}</b>
            </p>

            <p>
            Discount:
            <b>- {discount:,.2f} {currency}</b>
            </p>

            <p>
            Tax:
            <b>+ {tax:,.2f} {currency}</b>
            </p>

            <hr>

            <h1>
            TOTAL
            </h1>

            <h1>
            {total:,.2f} {currency}
            </h1>

            </div>
            """,
            unsafe_allow_html=True
        )

    if st.button(
        "💳 COMPLETE SALE",
        type="primary",
        use_container_width=True
    ):

        success, invoice, message = make_sale(
            discount,
            tax,
            total,
            payment
        )

        if success:

            st.session_state.cart = []

            st.success(
                f"✅ Sale completed successfully! Invoice: {invoice}"
            )

            st.rerun()

        else:

            st.error(
                message
            )


# ============================================================
# CART FUNCTION
# ============================================================

def add_cart(product_id):

    product = find_product(
        product_id
    )

    if not product:
        return

    if product["stock"] <= 0:
        return

    for item in st.session_state.cart:

        if item["product_id"] == product_id:

            if item["quantity"] < product["stock"]:

                item["quantity"] += 1

            return

    st.session_state.cart.append({
        "product_id": int(product["id"]),
        "name": product["name"],
        "sku": product["sku"],
        "price": float(product["price"]),
        "stock": int(product["stock"]),
        "quantity": 1
    })


# ============================================================
# COMPLETE SALE
# ============================================================

def make_sale(
    discount,
    tax,
    total,
    payment
):

    if st.session_state.role != "seller":

        return (
            False,
            "",
            "Only seller can make sales."
        )

    if not st.session_state.cart:

        return (
            False,
            "",
            "Cart is empty."
        )

    conn = connect_db()

    try:

        # ----------------------------------------------------
        # CHECK STOCK AGAIN
        # ----------------------------------------------------

        for item in st.session_state.cart:

            product = conn.execute("""
                SELECT *
                FROM products
                WHERE id=?
            """, (
                item["product_id"],
            )).fetchone()

            if not product:

                conn.rollback()
                conn.close()

                return (
                    False,
                    "",
                    f"Product not found: {item['name']}"
                )

            if product["stock"] < item["quantity"]:

                conn.rollback()
                conn.close()

                return (
                    False,
                    "",
                    f"Not enough stock for {item['name']}"
                )

        # ----------------------------------------------------
        # CREATE INVOICE
        # ----------------------------------------------------

        invoice = (
            "INV-"
            + datetime.now().strftime(
                "%Y%m%d%H%M%S"
            )
            + "-"
            + str(
                datetime.now().microsecond
            )[-4:]
        )

        subtotal = sum(
            item["price"] * item["quantity"]
            for item in st.session_state.cart
        )

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # ----------------------------------------------------
        # SALE
        # ----------------------------------------------------

        cursor = conn.execute("""
            INSERT INTO sales
            (
                invoice_no,
                seller,
                subtotal,
                discount,
                tax,
                total,
                payment_method,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice,
            st.session_state.user_name,
            subtotal,
            discount,
            tax,
            total,
            payment,
            now
        ))

        sale_id = cursor.lastrowid

        # ----------------------------------------------------
        # ITEMS
        # ----------------------------------------------------

        for item in st.session_state.cart:

            item_total = (
                item["price"]
                * item["quantity"]
            )

            conn.execute("""
                INSERT INTO sale_items
                (
                    sale_id,
                    product_id,
                    product_name,
                    sku,
                    quantity,
                    price,
                    total
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                sale_id,
                item["product_id"],
                item["name"],
                item["sku"],
                item["quantity"],
                item["price"],
                item_total
            ))

            # -----------------------------------------------
            # REMOVE STOCK
            # -----------------------------------------------

            conn.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE id=?
            """, (
                item["quantity"],
                item["product_id"]
            ))

            # -----------------------------------------------
            # HISTORY
            # -----------------------------------------------

            conn.execute("""
                INSERT INTO stock_history
                (
                    product_id,
                    sku,
                    product_name,
                    quantity,
                    action,
                    reason,
                    created_by,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["product_id"],
                item["sku"],
                item["name"],
                -item["quantity"],
                "SALE",
                invoice,
                st.session_state.user_name,
                now
            ))

        conn.commit()
        conn.close()

        return (
            True,
            invoice,
            "Sale completed."
        )

    except Exception as error:

        conn.rollback()
        conn.close()

        return (
            False,
            "",
            f"Sale error: {error}"
        )


# ============================================================
# SIDEBAR
# ============================================================

def show_sidebar():

    with st.sidebar:

        st.markdown(
            """
            <div style="
            text-align:center;
            font-size:55px;
            ">
            👟
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <h2 style="
            text-align:center;
            color:white;
            ">
            {get_setting(
                "store_name",
                "Shoe Shop POS"
            )}
            </h2>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        # ====================================================
        # ADMIN SIDEBAR
        # ====================================================

        if st.session_state.role == "admin":

            st.markdown(
                """
                <div class="admin-badge">
                🔐 ADMIN
                </div>
                """,
                unsafe_allow_html=True
            )

            st.write(
                f"👤 {st.session_state.user_name}"
            )

            st.divider()

            menu = st.radio(
                "ADMIN MENU",
                [
                    "📊 Dashboard",
                    "📦 Inventory",
                    "🧾 Sales History",
                    "📋 Stock History",
                    "⚙️ Settings",
                    "🚪 Logout"
                ],
                label_visibility="collapsed"
            )

            return menu

        # ====================================================
        # SELLER SIDEBAR
        # ====================================================

        if st.session_state.role == "seller":

            st.markdown(
                """
                <div class="seller-badge">
                🛒 SELLER
                </div>
                """,
                unsafe_allow_html=True
            )

            st.write(
                f"👤 {st.session_state.user_name}"
            )

            st.divider()

            menu = st.radio(
                "SELLER MENU",
                [
                    "🛒 New Sale",
                    "🚪 Logout"
                ],
                label_visibility="collapsed"
            )

            return menu


# ============================================================
# LOGOUT
# ============================================================

def logout():

    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_name = ""
    st.session_state.cart = []

    st.rerun()


# ============================================================
# MAIN APPLICATION
# ============================================================

if not st.session_state.logged_in:

    show_login()

else:

    selected_menu = show_sidebar()

    # ========================================================
    # ADMIN ROUTES
    # ========================================================

    if st.session_state.role == "admin":

        if selected_menu == "📊 Dashboard":

            admin_dashboard()

        elif selected_menu == "📦 Inventory":

            admin_inventory()

        elif selected_menu == "🧾 Sales History":

            sales_history()

        elif selected_menu == "📋 Stock History":

            stock_history_page()

        elif selected_menu == "⚙️ Settings":

            settings_page()

        elif selected_menu == "🚪 Logout":

            logout()

    # ========================================================
    # SELLER ROUTES
    # ========================================================

    elif st.session_state.role == "seller":

        if selected_menu == "🛒 New Sale":

            seller_pos()

        elif selected_menu == "🚪 Logout":

            logout()

    # ========================================================
    # INVALID SESSION
    # ========================================================

    else:

        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.user_name = ""

        st.rerun()
