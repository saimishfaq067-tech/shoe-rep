import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Shoe Shop POS",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CONFIG
# =========================================================

DB_FILE = "shoe_shop_pos.db"
ADMIN_PASSWORD = "viki90"

# =========================================================
# PROFESSIONAL CSS
# =========================================================

st.markdown("""
<style>

.stApp {
    background: #f5f7fb;
}

[data-testid="stSidebar"] {
    background: #111827;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.main-title {
    font-size: 34px;
    font-weight: 800;
    color: #111827;
    margin-bottom: 4px;
}

.sub-title {
    color: #6b7280;
    font-size: 15px;
    margin-bottom: 24px;
}

.metric-card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    min-height: 115px;
}

.metric-title {
    color: #6b7280;
    font-size: 13px;
    font-weight: 700;
}

.metric-value {
    color: #111827;
    font-size: 29px;
    font-weight: 800;
    margin-top: 8px;
}

.product-card {
    background: white;
    padding: 15px;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
    margin-bottom: 8px;
}

.product-name {
    font-size: 17px;
    font-weight: 700;
    color: #111827;
}

.product-info {
    color: #6b7280;
    font-size: 12px;
    margin-top: 5px;
}

.price {
    color: #111827;
    font-size: 19px;
    font-weight: 800;
}

.stock-good {
    color: #059669;
    font-weight: 700;
}

.stock-low {
    color: #dc2626;
    font-weight: 700;
}

.invoice-box {
    background: white;
    padding: 22px;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    margin-top: 10px;
    margin-bottom: 15px;
}

.section-box {
    background: white;
    padding: 22px;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    margin-bottom: 20px;
}

div.stButton > button {
    border-radius: 10px;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_database():

    conn = get_connection()
    cur = conn.cursor()

    # -----------------------------------------------------
    # PRODUCTS
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            brand TEXT,
            color TEXT,
            size TEXT,
            price REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 5,
            created_at TEXT
        )
    """)

    # -----------------------------------------------------
    # IMPORTANT DATABASE MIGRATION
    # -----------------------------------------------------

    existing_columns = [
        row["name"]
        for row in cur.execute(
            "PRAGMA table_info(products)"
        ).fetchall()
    ]

    if "min_stock" not in existing_columns:
        cur.execute("""
            ALTER TABLE products
            ADD COLUMN min_stock INTEGER DEFAULT 5
        """)

    if "category" not in existing_columns:
        cur.execute("""
            ALTER TABLE products
            ADD COLUMN category TEXT
        """)

    if "brand" not in existing_columns:
        cur.execute("""
            ALTER TABLE products
            ADD COLUMN brand TEXT
        """)

    if "color" not in existing_columns:
        cur.execute("""
            ALTER TABLE products
            ADD COLUMN color TEXT
        """)

    if "size" not in existing_columns:
        cur.execute("""
            ALTER TABLE products
            ADD COLUMN size TEXT
        """)

    if "price" not in existing_columns:
        cur.execute("""
            ALTER TABLE products
            ADD COLUMN price REAL DEFAULT 0
        """)

    if "stock" not in existing_columns:
        cur.execute("""
            ALTER TABLE products
            ADD COLUMN stock INTEGER DEFAULT 0
        """)

    if "created_at" not in existing_columns:
        cur.execute("""
            ALTER TABLE products
            ADD COLUMN created_at TEXT
        """)

    cur.execute("""
        UPDATE products
        SET min_stock = 5
        WHERE min_stock IS NULL
    """)

    # -----------------------------------------------------
    # SALES
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # SALE ITEMS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # STOCK HISTORY
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # SETTINGS
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cur.execute("""
        INSERT OR IGNORE INTO settings
        (key, value)
        VALUES (?, ?)
    """, (
        "store_name",
        "Shoe Shop POS"
    ))

    cur.execute("""
        INSERT OR IGNORE INTO settings
        (key, value)
        VALUES (?, ?)
    """, (
        "currency",
        "PKR"
    ))

    conn.commit()

    # =====================================================
    # CREATE 100 DEFAULT PRODUCTS
    # =====================================================

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
            "Clarks",
            "Reebok",
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
            "Red",
            "Grey",
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

            price = 2500 + ((i * 375) % 7500)
            stock = 10 + (i % 31)

            sku = f"SHOE-{i:04d}"
            name = f"{brand} {category} Shoe {i}"

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


# Start database
init_database()


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None

if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "cart" not in st.session_state:
    st.session_state.cart = []

if "last_invoice" not in st.session_state:
    st.session_state.last_invoice = None


# =========================================================
# SETTINGS FUNCTIONS
# =========================================================

def get_setting(key, default=""):

    conn = get_connection()

    row = conn.execute(
        "SELECT value FROM settings WHERE key = ?",
        (key,)
    ).fetchone()

    conn.close()

    if row:
        return row["value"]

    return default


def set_setting(key, value):

    conn = get_connection()

    conn.execute("""
        INSERT INTO settings
        (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
    """, (
        key,
        str(value)
    ))

    conn.commit()
    conn.close()


# =========================================================
# PRODUCT FUNCTIONS
# =========================================================

def get_products():

    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """, conn)

    conn.close()

    return df


def get_product(product_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM products
        WHERE id = ?
    """, (
        product_id,
    )).fetchone()

    conn.close()

    return row


def search_products(search_text):

    conn = get_connection()

    if not search_text.strip():

        df = pd.read_sql_query("""
            SELECT *
            FROM products
            ORDER BY name
        """, conn)

    else:

        value = f"%{search_text.strip()}%"

        df = pd.read_sql_query("""
            SELECT *
            FROM products
            WHERE
                name LIKE ?
                OR sku LIKE ?
                OR category LIKE ?
                OR brand LIKE ?
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


# =========================================================
# STOCK FUNCTIONS
# =========================================================

def add_stock(
    product_id,
    quantity,
    reason,
    username
):

    conn = get_connection()

    product = conn.execute("""
        SELECT *
        FROM products
        WHERE id = ?
    """, (
        product_id,
    )).fetchone()

    if not product:

        conn.close()

        return False

    new_stock = (
        int(product["stock"]) +
        int(quantity)
    )

    conn.execute("""
        UPDATE products
        SET stock = ?
        WHERE id = ?
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
        username,
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))

    conn.commit()
    conn.close()

    return True


# =========================================================
# UPDATE PRODUCT
# =========================================================

def update_product(
    product_id,
    name,
    sku,
    category,
    brand,
    color,
    size,
    price,
    min_stock
):

    conn = get_connection()

    try:

        conn.execute("""
            UPDATE products
            SET
                name = ?,
                sku = ?,
                category = ?,
                brand = ?,
                color = ?,
                size = ?,
                price = ?,
                min_stock = ?
            WHERE id = ?
        """, (
            name,
            sku,
            category,
            brand,
            color,
            size,
            price,
            min_stock,
            product_id
        ))

        conn.commit()
        conn.close()

        return True, "Product updated successfully."

    except sqlite3.IntegrityError:

        conn.close()

        return False, "SKU already exists."


# =========================================================
# DELETE PRODUCT
# =========================================================

def delete_product(product_id):

    conn = get_connection()

    conn.execute("""
        DELETE FROM products
        WHERE id = ?
    """, (
        product_id,
    ))

    conn.commit()
    conn.close()


# =========================================================
# LOGIN PAGE
# =========================================================

def login_page():

    st.markdown(
        "<div style='text-align:center;font-size:60px;'>👟</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<h1 style='text-align:center;'>Shoe Shop POS</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style='text-align:center;color:#6b7280;'>
        Professional Point of Sale System
        </p>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    col1, col2, col3 = st.columns(
        [1, 1.4, 1]
    )

    with col2:

        st.markdown("### 🔐 Login")

        login_type = st.radio(
            "Login as",
            [
                "Seller",
                "Admin"
            ],
            horizontal=True
        )

        # -------------------------------------------------
        # ADMIN
        # -------------------------------------------------

        if login_type == "Admin":

            password = st.text_input(
                "Admin Password",
                type="password"
            )

            if st.button(
                "Login as Admin",
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
                        "Incorrect admin password."
                    )

        # -------------------------------------------------
        # SELLER
        # -------------------------------------------------

        else:

            seller_name = st.text_input(
                "Seller Name",
                placeholder="Enter seller name"
            )

            st.caption(
                "Seller login does not require a password."
            )

            if st.button(
                "Login as Seller",
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


# =========================================================
# ADMIN DASHBOARD
# =========================================================

def admin_dashboard():

    # Security check
    if st.session_state.role != "admin":
        st.error("Access denied.")
        return

    st.markdown(
        "<div class='main-title'>📊 Admin Dashboard</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='sub-title'>
        Complete business overview and management
        </div>
        """,
        unsafe_allow_html=True
    )

    conn = get_connection()

    total_products = conn.execute("""
        SELECT COUNT(*)
        FROM products
    """).fetchone()[0]

    total_stock = conn.execute("""
        SELECT COALESCE(
            SUM(stock),
            0
        )
        FROM products
    """).fetchone()[0]

    # IMPORTANT:
    # Use COALESCE so old databases work safely.
    low_stock = conn.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE stock <= COALESCE(min_stock, 5)
    """).fetchone()[0]

    today_data = conn.execute("""
        SELECT
            COALESCE(SUM(total), 0),
            COUNT(*)
        FROM sales
        WHERE DATE(created_at)
        = DATE('now', 'localtime')
    """).fetchone()

    total_sales = conn.execute("""
        SELECT COALESCE(
            SUM(total),
            0
        )
        FROM sales
    """).fetchone()[0]

    total_transactions = conn.execute("""
        SELECT COUNT(*)
        FROM sales
    """).fetchone()[0]

    conn.close()

    currency = get_setting(
        "currency",
        "PKR"
    )

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">
                    TOTAL PRODUCTS
                </div>
                <div class="metric-value">
                    {total_products}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">
                    TOTAL STOCK
                </div>
                <div class="metric-value">
                    {total_stock}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">
                    LOW STOCK ITEMS
                </div>
                <div class="metric-value">
                    {low_stock}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">
                    TODAY SALES
                </div>
                <div class="metric-value">
                    {today_data[0]:,.0f}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")

    # -----------------------------------------------------
    # BUSINESS SUMMARY
    # -----------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 💰 Business Sales")

        st.metric(
            "All Time Sales",
            f"{total_sales:,.0f} {currency}"
        )

        st.metric(
            "Total Transactions",
            total_transactions
        )

    with col2:

        st.markdown("### ⚠️ Stock Alerts")

        if low_stock > 0:

            st.warning(
                f"{low_stock} product(s) need stock attention."
            )

        else:

            st.success(
                "All products have healthy stock levels."
            )

    # -----------------------------------------------------
    # LOW STOCK TABLE
    # -----------------------------------------------------

    st.markdown("### 📦 Low Stock Products")

    products = get_products()

    low_products = products[
        products["stock"] <=
        products["min_stock"].fillna(5)
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


# =========================================================
# ADMIN INVENTORY
# =========================================================

def admin_inventory():

    if st.session_state.role != "admin":

        st.error("Access denied.")
        return

    st.markdown(
        "<div class='main-title'>📦 Inventory Management</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='sub-title'>
        Add products, manage stock and update product information.
        </div>
        """,
        unsafe_allow_html=True
    )

    tab1, tab2, tab3 = st.tabs([
        "➕ Add Product",
        "📥 Stock In",
        "📋 Products"
    ])

    # =====================================================
    # ADD PRODUCT
    # =====================================================

    with tab1:

        st.markdown("### Add New Product")

        with st.form("add_product_form"):

            col1, col2 = st.columns(2)

            with col1:

                name = st.text_input(
                    "Product Name"
                )

                sku = st.text_input(
                    "SKU / Barcode"
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

            with col2:

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
                    "Minimum Stock Alert",
                    min_value=0,
                    value=5,
                    step=1
                )

            submitted = st.form_submit_button(
                "➕ Add Product",
                type="primary",
                use_container_width=True
            )

            if submitted:

                if not name.strip():

                    st.error(
                        "Product name is required."
                    )

                elif not sku.strip():

                    st.error(
                        "SKU is required."
                    )

                else:

                    conn = get_connection()

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

    # =====================================================
    # STOCK IN
    # =====================================================

    with tab2:

        st.markdown("### 📥 Add Stock")

        products = get_products()

        if products.empty:

            st.info(
                "No products available."
            )

        else:

            product_options = {}

            for _, row in products.iterrows():

                label = (
                    f"{row['sku']} — "
                    f"{row['name']} | "
                    f"Stock: {row['stock']}"
                )

                product_options[label] = int(
                    row["id"]
                )

            selected_label = st.selectbox(
                "Select Product",
                list(product_options.keys())
            )

            selected_id = product_options[
                selected_label
            ]

            product = get_product(
                selected_id
            )

            st.markdown(
                f"""
                <div class="product-card">
                    <div class="product-name">
                        {product["name"]}
                    </div>

                    <div class="product-info">
                        SKU: {product["sku"]}
                        |
                        Category: {product["category"]}
                        |
                        Current Stock: {product["stock"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            quantity = st.number_input(
                "Quantity to Add",
                min_value=1,
                value=1,
                step=1
            )

            reason = st.text_input(
                "Reason",
                placeholder="New supplier delivery"
            )

            if st.button(
                "📥 Add Stock",
                type="primary"
            ):

                if not reason.strip():

                    reason = "Stock added"

                success = add_stock(
                    selected_id,
                    quantity,
                    reason,
                    st.session_state.user_name
                )

                if success:

                    st.success(
                        f"{quantity} units added successfully."
                    )

                    st.rerun()

    # =====================================================
    # PRODUCTS
    # =====================================================

    with tab3:

        products = get_products()

        search = st.text_input(
            "🔎 Search products",
            placeholder=(
                "Search name, SKU, brand, category, color or size..."
            )
        )

        if search:

            mask = products.astype(str).apply(
                lambda row: row.str.contains(
                    search,
                    case=False,
                    na=False
                ).any(),
                axis=1
            )

            products = products[mask]

        if products.empty:

            st.info(
                "No products found."
            )

        else:

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

            # -------------------------------------------------
            # EDIT
            # -------------------------------------------------

            st.markdown("### ✏️ Edit Product")

            edit_options = {}

            for _, row in products.iterrows():

                edit_options[
                    f"{row['sku']} — {row['name']}"
                ] = int(row["id"])

            selected_edit = st.selectbox(
                "Select Product",
                list(edit_options.keys()),
                key="edit_product"
            )

            edit_id = edit_options[
                selected_edit
            ]

            product = get_product(
                edit_id
            )

            with st.form("edit_form"):

                col1, col2 = st.columns(2)

                with col1:

                    edit_name = st.text_input(
                        "Product Name",
                        value=product["name"]
                    )

                    edit_sku = st.text_input(
                        "SKU",
                        value=product["sku"]
                    )

                    edit_category = st.text_input(
                        "Category",
                        value=product["category"] or ""
                    )

                    edit_brand = st.text_input(
                        "Brand",
                        value=product["brand"] or ""
                    )

                with col2:

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
                        value=float(
                            product["price"] or 0
                        ),
                        step=100.0
                    )

                    edit_min_stock = st.number_input(
                        "Minimum Stock",
                        min_value=0,
                        value=int(
                            product["min_stock"] or 5
                        ),
                        step=1
                    )

                save = st.form_submit_button(
                    "💾 Save Changes",
                    type="primary"
                )

                if save:

                    success, message = update_product(
                        edit_id,
                        edit_name.strip(),
                        edit_sku.strip(),
                        edit_category.strip(),
                        edit_brand.strip(),
                        edit_color.strip(),
                        edit_size.strip(),
                        edit_price,
                        edit_min_stock
                    )

                    if success:

                        st.success(
                            message
                        )

                        st.rerun()

                    else:

                        st.error(
                            message
                        )

            # -------------------------------------------------
            # DELETE
            # -------------------------------------------------

            st.markdown("### 🗑️ Delete Product")

            confirm = st.checkbox(
                "I understand that deleting this product cannot be undone."
            )

            if confirm:

                if st.button(
                    "🗑️ Delete Selected Product"
                ):

                    delete_product(
                        edit_id
                    )

                    st.success(
                        "Product deleted successfully."
                    )

                    st.rerun()


# =========================================================
# SALES HISTORY
# =========================================================

def sales_history():

    if st.session_state.role != "admin":

        st.error("Access denied.")
        return

    st.markdown(
        "<div class='main-title'>🧾 Sales History</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='sub-title'>
        Review all completed seller transactions.
        </div>
        """,
        unsafe_allow_html=True
    )

    conn = get_connection()

    sales = pd.read_sql_query("""
        SELECT
            id,
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
            "No sales recorded yet."
        )

        return

    search = st.text_input(
        "🔎 Search invoice or seller"
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

    if not sales.empty:

        st.markdown("### 📄 Invoice Details")

        invoice = st.selectbox(
            "Select Invoice",
            sales["invoice_no"].tolist()
        )

        conn = get_connection()

        sale = conn.execute("""
            SELECT *
            FROM sales
            WHERE invoice_no = ?
        """, (
            invoice,
        )).fetchone()

        items = pd.read_sql_query("""
            SELECT
                product_name,
                sku,
                quantity,
                price,
                total
            FROM sale_items
            WHERE sale_id = ?
        """, conn, params=(
            sale["id"],
        ))

        conn.close()

        st.markdown(
            f"""
            <div class="invoice-box">

            <h2>
            {get_setting("store_name", "Shoe Shop POS")}
            </h2>

            <p>
            <b>Invoice:</b> {sale["invoice_no"]}
            <br>
            <b>Seller:</b> {sale["seller"]}
            <br>
            <b>Date:</b> {sale["created_at"]}
            <br>
            <b>Payment:</b> {sale["payment_method"]}
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )

        st.dataframe(
            items,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Invoice Total",
            f"""
            {sale["total"]:,.2f}
            {get_setting("currency", "PKR")}
            """
        )


# =========================================================
# STOCK HISTORY
# =========================================================

def stock_history_page():

    if st.session_state.role != "admin":

        st.error("Access denied.")
        return

    st.markdown(
        "<div class='main-title'>📋 Stock History</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='sub-title'>
        Track stock additions and sales stock deductions.
        </div>
        """,
        unsafe_allow_html=True
    )

    conn = get_connection()

    history = pd.read_sql_query("""
        SELECT
            id,
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


# =========================================================
# SETTINGS
# =========================================================

def settings_page():

    if st.session_state.role != "admin":

        st.error("Access denied.")
        return

    st.markdown(
        "<div class='main-title'>⚙️ Settings</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='sub-title'>
        Manage your store configuration.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-box">',
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
        "💾 Save Settings",
        type="primary"
    ):

        set_setting(
            "store_name",
            store_name
        )

        set_setting(
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

    st.markdown("### 🔐 Security")

    st.info(
        "Current admin password is configured in app.py."
    )


# =========================================================
# SELLER POS
# =========================================================

def seller_pos():

    # Security
    if st.session_state.role != "seller":

        st.error("Access denied.")
        return

    st.markdown(
        "<div class='main-title'>🛒 New Sale</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class='sub-title'>
        Seller:
        <b>{st.session_state.user_name}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    # =====================================================
    # SEARCH
    # =====================================================

    search = st.text_input(
        "🔎 Search Product",
        placeholder=(
            "Search name, SKU, brand, category, color or size..."
        ),
        key="seller_search"
    )

    products = search_products(
        search
    )

    if products.empty:

        st.warning(
            "No matching products found."
        )

    else:

        st.write(
            f"**{len(products)} product(s) found**"
        )

        for _, product in products.head(50).iterrows():

            c1, c2, c3, c4 = st.columns(
                [3.5, 1.8, 1.3, 1]
            )

            with c1:

                st.markdown(
                    f"""
                    <div class="product-card">

                    <div class="product-name">
                    {product["name"]}
                    </div>

                    <div class="product-info">
                    SKU: {product["sku"]}
                    <br>
                    {product["brand"]}
                    •
                    {product["category"]}
                    •
                    Size {product["size"]}
                    •
                    {product["color"]}
                    </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with c2:

                st.markdown(
                    f"""
                    <div style="padding-top:20px;">
                    <div class="price">
                    {product["price"]:,.0f}
                    {get_setting("currency", "PKR")}
                    </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with c3:

                if product["stock"] <= product["min_stock"]:

                    st.markdown(
                        f"""
                        <div style="padding-top:20px;">
                        <span class="stock-low">
                        Stock: {product["stock"]}
                        </span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                else:

                    st.markdown(
                        f"""
                        <div style="padding-top:20px;">
                        <span class="stock-good">
                        Stock: {product["stock"]}
                        </span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            with c4:

                if product["stock"] > 0:

                    if st.button(
                        "Add",
                        key=f"seller_add_{product['id']}"
                    ):

                        add_to_cart(
                            int(product["id"])
                        )

                        st.rerun()

                else:

                    st.error(
                        "Out"
                    )

    # =====================================================
    # CART
    # =====================================================

    st.divider()

    st.markdown("## 🛍️ Current Cart")

    if not st.session_state.cart:

        st.info(
            "Cart is empty. Search for a product and click Add."
        )

        return

    subtotal = 0

    for index, item in enumerate(
        st.session_state.cart
    ):

        c1, c2, c3, c4, c5 = st.columns(
            [3, 1.3, 1.3, 1.4, 0.7]
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
                f"{item['price']:,.0f}"
            )

        with c3:

            quantity = st.number_input(
                "Qty",
                min_value=1,
                max_value=max(
                    1,
                    int(item["stock"])
                ),
                value=int(item["quantity"]),
                key=f"cart_qty_{index}"
            )

            st.session_state.cart[
                index
            ]["quantity"] = quantity

        with c4:

            total = (
                item["price"] *
                quantity
            )

            subtotal += total

            st.write(
                f"**{total:,.0f}**"
            )

        with c5:

            if st.button(
                "✕",
                key=f"remove_cart_{index}"
            ):

                st.session_state.cart.pop(
                    index
                )

                st.rerun()

    # =====================================================
    # CHECKOUT
    # =====================================================

    st.divider()

    c1, c2 = st.columns(2)

    with c1:

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

        payment_method = st.selectbox(
            "Payment Method",
            [
                "Cash",
                "Card",
                "Bank Transfer",
                "JazzCash",
                "Easypaisa"
            ]
        )

    with c2:

        after_discount = max(
            0,
            subtotal - discount
        )

        tax_amount = (
            after_discount *
            tax_percent /
            100
        )

        grand_total = (
            after_discount +
            tax_amount
        )

        st.markdown(
            f"""
            <div class="invoice-box">

            <h3>Sale Summary</h3>

            <p>
            Subtotal:
            <b>{subtotal:,.2f}</b>
            </p>

            <p>
            Discount:
            <b>- {discount:,.2f}</b>
            </p>

            <p>
            Tax:
            <b>+ {tax_amount:,.2f}</b>
            </p>

            <hr>

            <h2>
            Total:
            {grand_total:,.2f}
            {get_setting("currency", "PKR")}
            </h2>

            </div>
            """,
            unsafe_allow_html=True
        )

    if st.button(
        "💳 COMPLETE SALE",
        type="primary",
        use_container_width=True
    ):

        success, invoice_no, message = complete_sale(
            discount,
            tax_amount,
            grand_total,
            payment_method
        )

        if success:

            st.session_state.last_invoice = invoice_no
            st.session_state.cart = []

            st.success(
                f"Sale completed successfully. Invoice: {invoice_no}"
            )

            st.rerun()

        else:

            st.error(
                message
            )


# =========================================================
# CART ADD
# =========================================================

def add_to_cart(product_id):

    product = get_product(
        product_id
    )

    if not product:
        return

    if product["stock"] <= 0:

        st.error(
            "Product is out of stock."
        )

        return

    for item in st.session_state.cart:

        if item["product_id"] == product_id:

            if item["quantity"] >= product["stock"]:

                st.warning(
                    "Available stock limit reached."
                )

                return

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


# =========================================================
# COMPLETE SALE
# =========================================================

def complete_sale(
    discount,
    tax_amount,
    grand_total,
    payment_method
):

    # Only seller can create sales
    if st.session_state.role != "seller":

        return (
            False,
            None,
            "Only sellers can create sales."
        )

    if not st.session_state.cart:

        return (
            False,
            None,
            "Cart is empty."
        )

    conn = get_connection()

    try:

        # -------------------------------------------------
        # FINAL STOCK CHECK
        # -------------------------------------------------

        for item in st.session_state.cart:

            product = conn.execute("""
                SELECT *
                FROM products
                WHERE id = ?
            """, (
                item["product_id"],
            )).fetchone()

            if not product:

                conn.rollback()
                conn.close()

                return (
                    False,
                    None,
                    f"Product not found: {item['name']}"
                )

            if product["stock"] < item["quantity"]:

                conn.rollback()
                conn.close()

                return (
                    False,
                    None,
                    f"Not enough stock for {item['name']}."
                )

        # -------------------------------------------------
        # INVOICE
        # -------------------------------------------------

        invoice_no = (
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
            item["price"] *
            item["quantity"]
            for item in st.session_state.cart
        )

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # -------------------------------------------------
        # SALE
        # -------------------------------------------------

        cur = conn.execute("""
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
            invoice_no,
            st.session_state.user_name,
            subtotal,
            discount,
            tax_amount,
            grand_total,
            payment_method,
            now
        ))

        sale_id = cur.lastrowid

        # -------------------------------------------------
        # ITEMS + STOCK
        # -------------------------------------------------

        for item in st.session_state.cart:

            item_total = (
                item["price"] *
                item["quantity"]
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

            conn.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
            """, (
                item["quantity"],
                item["product_id"]
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
                item["product_id"],
                item["sku"],
                item["name"],
                -item["quantity"],
                "SALE",
                f"Invoice {invoice_no}",
                st.session_state.user_name,
                now
            ))

        conn.commit()
        conn.close()

        return (
            True,
            invoice_no,
            "Sale completed successfully."
        )

    except Exception as e:

        conn.rollback()
        conn.close()

        return (
            False,
            None,
            f"Sale failed: {str(e)}"
        )


# =========================================================
# SIDEBAR
# =========================================================

def sidebar():

    with st.sidebar:

        st.markdown(
            """
            <div style="
                text-align:center;
                font-size:48px;
                margin-bottom:5px;
            ">
            👟
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <h2 style="text-align:center;">
            {get_setting(
                "store_name",
                "Shoe Shop POS"
            )}
            </h2>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        # =================================================
        # ADMIN MENU
        # =================================================

        if st.session_state.role == "admin":

            st.markdown(
                """
                <div style="
                    background:#2563eb;
                    padding:7px;
                    border-radius:20px;
                    text-align:center;
                    font-weight:700;
                ">
                ADMIN
                </div>
                """,
                unsafe_allow_html=True
            )

            st.write(
                f"👤 {st.session_state.user_name}"
            )

            menu = st.radio(
                "Admin Menu",
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

        # =================================================
        # SELLER MENU
        # =================================================

        else:

            st.markdown(
                """
                <div style="
                    background:#059669;
                    padding:7px;
                    border-radius:20px;
                    text-align:center;
                    font-weight:700;
                ">
                SELLER
                </div>
                """,
                unsafe_allow_html=True
            )

            st.write(
                f"👤 {st.session_state.user_name}"
            )

            menu = st.radio(
                "Seller Menu",
                [
                    "🛒 New Sale",
                    "🚪 Logout"
                ],
                label_visibility="collapsed"
            )

        return menu


# =========================================================
# LOGOUT
# =========================================================

def logout():

    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_name = None
    st.session_state.cart = []
    st.session_state.last_invoice = None

    st.rerun()


# =========================================================
# MAIN APPLICATION
# =========================================================

if not st.session_state.logged_in:

    login_page()

else:

    menu = sidebar()

    # =====================================================
    # ADMIN
    # =====================================================

    if st.session_state.role == "admin":

        if menu == "📊 Dashboard":

            admin_dashboard()

        elif menu == "📦 Inventory":

            admin_inventory()

        elif menu == "🧾 Sales History":

            sales_history()

        elif menu == "📋 Stock History":

            stock_history_page()

        elif menu == "⚙️ Settings":

            settings_page()

        elif menu == "🚪 Logout":

            logout()

    # =====================================================
    # SELLER
    # =====================================================

    elif st.session_state.role == "seller":

        if menu == "🛒 New Sale":

            seller_pos()

        elif menu == "🚪 Logout":

            logout()

    # =====================================================
    # INVALID ROLE
    # =====================================================

    else:

        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.user_name = None

        st.error(
            "Invalid session. Please login again."
        )

        st.rerun()
