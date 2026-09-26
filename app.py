import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import string

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
# CSS
# =========================================================

st.markdown("""
<style>

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.stApp {
    background: #f5f7fb;
}

section[data-testid="stSidebar"] {
    background: #111827;
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

.main-title {
    font-size: 34px;
    font-weight: 800;
    color: #111827;
    margin-bottom: 5px;
}

.subtitle {
    color: #6b7280;
    font-size: 15px;
    margin-bottom: 25px;
}

.card {
    background: white;
    border-radius: 15px;
    padding: 20px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 15px rgba(0,0,0,0.04);
    margin-bottom: 15px;
}

.metric-card {
    background: white;
    border-radius: 15px;
    padding: 20px;
    border: 1px solid #e5e7eb;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.04);
}

.metric-title {
    color: #6b7280;
    font-size: 14px;
}

.metric-value {
    color: #111827;
    font-size: 28px;
    font-weight: 800;
    margin-top: 5px;
}

.product-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 12px;
}

.product-name {
    font-size: 19px;
    font-weight: 800;
    color: #111827;
}

.product-info {
    color: #6b7280;
    font-size: 13px;
    margin-top: 5px;
}

.price {
    font-size: 21px;
    font-weight: 800;
    color: #111827;
}

.stock {
    font-size: 14px;
    font-weight: 700;
}

.cart-box {
    background: white;
    border-radius: 15px;
    padding: 20px;
    border: 1px solid #e5e7eb;
}

.admin-badge {
    background: #2563eb;
    padding: 7px 12px;
    border-radius: 20px;
    font-weight: 700;
    color: white;
    display: inline-block;
}

.seller-badge {
    background: #059669;
    padding: 7px 12px;
    border-radius: 20px;
    font-weight: 700;
    color: white;
    display: inline-block;
}

.search-box {
    background: white;
    padding: 15px;
    border-radius: 15px;
    border: 1px solid #e5e7eb;
    margin-bottom: 20px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# DATABASE
# =========================================================

DB_NAME = "shoe_shop_pos.db"


def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# =========================================================
# DATABASE HELPERS
# =========================================================

def table_exists(conn, table_name):
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    ).fetchone()
    return row is not None


def get_columns(conn, table_name):
    if not table_exists(conn, table_name):
        return set()

    rows = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return {row["name"] for row in rows}


def add_missing_column(conn, table_name, column_name, definition):
    columns = get_columns(conn, table_name)

    if column_name not in columns:
        conn.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    conn = get_db()

    # -----------------------------------------------------
    # PRODUCTS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE,
            name TEXT,
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
    # SALES
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE,
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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            sku TEXT,
            quantity INTEGER DEFAULT 1,
            price REAL DEFAULT 0,
            total REAL DEFAULT 0
        )
    """)

    # -----------------------------------------------------
    # STOCK HISTORY
    # -----------------------------------------------------

    conn.execute("""
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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()

    # =====================================================
    # MIGRATION
    # =====================================================
    # This fixes old databases automatically.
    # =====================================================

    product_columns = {
        "sku": "TEXT",
        "name": "TEXT",
        "category": "TEXT",
        "brand": "TEXT",
        "color": "TEXT",
        "size": "TEXT",
        "price": "REAL DEFAULT 0",
        "stock": "INTEGER DEFAULT 0",
        "min_stock": "INTEGER DEFAULT 5",
        "created_at": "TEXT"
    }

    for column, definition in product_columns.items():
        add_missing_column(
            conn,
            "products",
            column,
            definition
        )

    sales_columns = {
        "invoice_no": "TEXT",
        "seller": "TEXT",
        "subtotal": "REAL DEFAULT 0",
        "discount": "REAL DEFAULT 0",
        "tax": "REAL DEFAULT 0",
        "total": "REAL DEFAULT 0",
        "payment_method": "TEXT",
        "created_at": "TEXT"
    }

    for column, definition in sales_columns.items():
        add_missing_column(
            conn,
            "sales",
            column,
            definition
        )

    sale_item_columns = {
        "sale_id": "INTEGER",
        "product_id": "INTEGER",
        "product_name": "TEXT",
        "sku": "TEXT",
        "quantity": "INTEGER DEFAULT 1",
        "price": "REAL DEFAULT 0",
        "total": "REAL DEFAULT 0"
    }

    for column, definition in sale_item_columns.items():
        add_missing_column(
            conn,
            "sale_items",
            column,
            definition
        )

    stock_columns = {
        "product_id": "INTEGER",
        "sku": "TEXT",
        "product_name": "TEXT",
        "quantity": "INTEGER",
        "action": "TEXT",
        "reason": "TEXT",
        "created_by": "TEXT",
        "created_at": "TEXT"
    }

    for column, definition in stock_columns.items():
        add_missing_column(
            conn,
            "stock_history",
            column,
            definition
        )

    # -----------------------------------------------------
    # DEFAULT SETTINGS
    # -----------------------------------------------------

    conn.execute("""
        INSERT OR IGNORE INTO settings(key, value)
        VALUES('store_name', 'Shoe Shop POS')
    """)

    conn.execute("""
        INSERT OR IGNORE INTO settings(key, value)
        VALUES('currency', 'PKR')
    """)

    conn.commit()

    # -----------------------------------------------------
    # SAMPLE PRODUCTS
    # -----------------------------------------------------

    count = conn.execute(
        "SELECT COUNT(*) AS c FROM products"
    ).fetchone()["c"]

    if count == 0:
        create_sample_products(conn)

    conn.commit()

    return conn


# =========================================================
# SAMPLE PRODUCTS
# =========================================================

def create_sample_products(conn):

    brands = [
        "Nike",
        "Adidas",
        "Puma",
        "Skechers",
        "Bata",
        "Servis",
        "Clarks",
        "Hush Puppies",
        "Gucci",
        "Urban Walk"
    ]

    categories = [
        "Running",
        "Casual",
        "Formal",
        "Sports",
        "Sneakers",
        "Boots",
        "Sandals"
    ]

    colors = [
        "Black",
        "White",
        "Blue",
        "Brown",
        "Grey",
        "Red"
    ]

    sizes = [
        "39",
        "40",
        "41",
        "42",
        "43",
        "44"
    ]

    shoe_types = [
        "Classic Runner",
        "Street Walker",
        "Premium Sneaker",
        "Comfort Shoe",
        "Sport Pro",
        "Urban Sneaker",
        "Leather Classic",
        "Daily Comfort",
        "Active Runner",
        "Modern Walk"
    ]

    for i in range(1, 101):

        brand = brands[(i - 1) % len(brands)]
        category = categories[(i - 1) % len(categories)]
        color = colors[(i - 1) % len(colors)]
        size = sizes[(i - 1) % len(sizes)]
        shoe_type = shoe_types[(i - 1) % len(shoe_types)]

        name = f"{brand} {shoe_type} {i}"
        sku = f"SHOE-{i:04d}"

        price = random.randint(2500, 15000)
        stock = random.randint(5, 50)

        conn.execute("""
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
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))


# =========================================================
# SETTINGS HELPERS
# =========================================================

def get_setting(conn, key, default=""):

    row = conn.execute(
        "SELECT value FROM settings WHERE key=?",
        (key,)
    ).fetchone()

    if row:
        return row["value"]

    return default


def set_setting(conn, key, value):

    conn.execute("""
        INSERT INTO settings(key, value)
        VALUES(?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value=excluded.value
    """, (key, value))

    conn.commit()


# =========================================================
# UTILITY
# =========================================================

def money(value, currency="PKR"):
    return f"{currency} {float(value):,.2f}"


def generate_invoice():

    now = datetime.now()

    random_part = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=5)
    )

    return f"INV-{now.strftime('%Y%m%d%H%M%S')}-{random_part}"


# =========================================================
# SESSION
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "cart" not in st.session_state:
    st.session_state.cart = []


# =========================================================
# DATABASE
# =========================================================

conn = init_db()

store_name = get_setting(
    conn,
    "store_name",
    "Shoe Shop POS"
)

currency = get_setting(
    conn,
    "currency",
    "PKR"
)


# =========================================================
# LOGIN
# =========================================================

def login_page():

    st.markdown(
        "<div style='text-align:center;'>"
        "<div style='font-size:70px;'>👟</div>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<h1 style='text-align:center;'>Shoe Shop POS</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center;color:#6b7280;'>"
        "Professional Point of Sale System"
        "</p>",
        unsafe_allow_html=True
    )

    st.write("")

    left, center, right = st.columns([1, 2, 1])

    with center:

        login_type = st.radio(
            "Login As",
            ["Seller", "Admin"],
            horizontal=True
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
                    st.session_state.role = "admin"
                    st.session_state.user_name = "Admin"

                    st.rerun()

                else:
                    st.error("Incorrect admin password.")

        else:

            seller_name = st.text_input(
                "Seller Name"
            )

            if st.button(
                "Login as Seller",
                use_container_width=True
            ):

                if seller_name.strip():

                    st.session_state.logged_in = True
                    st.session_state.role = "seller"
                    st.session_state.user_name = seller_name.strip()

                    st.session_state.cart = []

                    st.rerun()

                else:
                    st.warning("Please enter seller name.")


# =========================================================
# LOGOUT
# =========================================================

def logout():

    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_name = ""
    st.session_state.cart = []

    st.rerun()


# =========================================================
# ADMIN GUARD
# =========================================================

def require_admin():

    if (
        not st.session_state.logged_in
        or st.session_state.role != "admin"
    ):
        st.error("Admin access required.")
        return False

    return True


# =========================================================
# SELLER GUARD
# =========================================================

def require_seller():

    if (
        not st.session_state.logged_in
        or st.session_state.role != "seller"
    ):
        st.error("Seller access required.")
        return False

    return True


# =========================================================
# ADMIN DASHBOARD
# =========================================================

def admin_dashboard():

    if not require_admin():
        return

    st.markdown(
        "<div class='main-title'>Admin Dashboard</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='subtitle'>Complete business overview and management</div>",
        unsafe_allow_html=True
    )

    total_products = conn.execute("""
        SELECT COUNT(*) AS c
        FROM products
    """).fetchone()["c"]

    total_stock = conn.execute("""
        SELECT COALESCE(SUM(stock),0) AS c
        FROM products
    """).fetchone()["c"]

    low_stock = conn.execute("""
        SELECT COUNT(*) AS c
        FROM products
        WHERE stock <= COALESCE(min_stock,5)
    """).fetchone()["c"]

    today_sales = conn.execute("""
        SELECT COALESCE(SUM(total),0) AS c
        FROM sales
        WHERE date(created_at)=date('now','localtime')
    """).fetchone()["c"]

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Products</div>
            <div class="metric-value">{total_products}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Stock Quantity</div>
            <div class="metric-value">{total_stock}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Low Stock Products</div>
            <div class="metric-value">{low_stock}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Today's Sales</div>
            <div class="metric-value">{money(today_sales, currency)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    left, right = st.columns(2)

    with left:

        st.markdown("### 📊 Sales Summary")

        total_sales = conn.execute("""
            SELECT COALESCE(SUM(total),0) AS c
            FROM sales
        """).fetchone()["c"]

        total_orders = conn.execute("""
            SELECT COUNT(*) AS c
            FROM sales
        """).fetchone()["c"]

        st.markdown(f"""
        <div class="card">
            <b>Total Sales:</b> {money(total_sales, currency)}<br><br>
            <b>Total Orders:</b> {total_orders}
        </div>
        """, unsafe_allow_html=True)

    with right:

        st.markdown("### ⚠️ Low Stock")

        low_df = pd.read_sql_query("""
            SELECT
                sku AS SKU,
                name AS Product,
                category AS Category,
                price AS Price,
                stock AS Stock,
                min_stock AS Alert_Level
            FROM products
            WHERE stock <= COALESCE(min_stock,5)
            ORDER BY stock ASC
            LIMIT 10
        """, conn)

        if low_df.empty:
            st.success("No low-stock products.")
        else:
            st.dataframe(
                low_df,
                use_container_width=True,
                hide_index=True
            )


# =========================================================
# ADMIN INVENTORY
# =========================================================

def admin_inventory():

    if not require_admin():
        return

    st.markdown(
        "<div class='main-title'>Inventory Management</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='subtitle'>Manage products, prices and stock quantity</div>",
        unsafe_allow_html=True
    )

    tab1, tab2, tab3 = st.tabs([
        "➕ Add Product",
        "📦 Add Stock",
        "🛠️ Manage Products"
    ])

    # =====================================================
    # ADD PRODUCT
    # =====================================================

    with tab1:

        st.markdown("### Add New Product")

        c1, c2 = st.columns(2)

        with c1:

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
                    "Running",
                    "Casual",
                    "Formal",
                    "Sports",
                    "Sneakers",
                    "Boots",
                    "Sandals",
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
                step=100.0
            )

            stock = st.number_input(
                "Initial Stock Quantity",
                min_value=0,
                step=1
            )

            min_stock = st.number_input(
                "Low Stock Alert Level",
                min_value=0,
                value=5,
                step=1
            )

        if st.button(
            "➕ Add Product",
            type="primary",
            use_container_width=True
        ):

            if not name.strip():
                st.error("Product name is required.")

            elif not sku.strip():
                st.error("SKU / Barcode is required.")

            else:

                try:

                    conn.execute("""
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

                    conn.commit()

                    st.success(
                        f"{name} added successfully."
                    )

                except sqlite3.IntegrityError:
                    st.error(
                        "This SKU already exists."
                    )

    # =====================================================
    # ADD STOCK
    # =====================================================

    with tab2:

        st.markdown("### Add Stock")

        products = conn.execute("""
            SELECT
                id,
                sku,
                name,
                stock
            FROM products
            ORDER BY name
        """).fetchall()

        if not products:

            st.warning("No products available.")

        else:

            product_options = {
                f"{p['sku']} — {p['name']} — Current Stock: {p['stock']}":
                p["id"]
                for p in products
            }

            selected_label = st.selectbox(
                "Select Product",
                list(product_options.keys())
            )

            selected_id = product_options[selected_label]

            quantity = st.number_input(
                "Quantity to Add",
                min_value=1,
                value=1,
                step=1
            )

            reason = st.text_input(
                "Reason",
                value="New Stock"
            )

            if st.button(
                "📦 Add Stock",
                type="primary",
                use_container_width=True
            ):

                product = conn.execute("""
                    SELECT *
                    FROM products
                    WHERE id=?
                """, (selected_id,)).fetchone()

                new_stock = (
                    int(product["stock"]) +
                    int(quantity)
                )

                conn.execute("""
                    UPDATE products
                    SET stock=?
                    WHERE id=?
                """, (
                    new_stock,
                    selected_id
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
                    product["id"],
                    product["sku"],
                    product["name"],
                    quantity,
                    "STOCK IN",
                    reason,
                    "Admin",
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                ))

                conn.commit()

                st.success(
                    f"Stock updated. New quantity: {new_stock}"
                )

    # =====================================================
    # MANAGE PRODUCTS
    # =====================================================

    with tab3:

        st.markdown("### All Products")

        search = st.text_input(
            "🔎 Search Products",
            placeholder="Search by name, SKU, brand, category, color or size..."
        )

        if search.strip():

            like = f"%{search.strip()}%"

            df = pd.read_sql_query("""
                SELECT
                    id AS ID,
                    sku AS SKU,
                    name AS Product,
                    brand AS Brand,
                    category AS Category,
                    color AS Color,
                    size AS Size,
                    price AS Price,
                    stock AS Stock,
                    min_stock AS Alert_Level
                FROM products
                WHERE
                    name LIKE ?
                    OR sku LIKE ?
                    OR brand LIKE ?
                    OR category LIKE ?
                    OR color LIKE ?
                    OR size LIKE ?
                ORDER BY name
            """, conn, params=[
                like,
                like,
                like,
                like,
                like,
                like
            ])

        else:

            df = pd.read_sql_query("""
                SELECT
                    id AS ID,
                    sku AS SKU,
                    name AS Product,
                    brand AS Brand,
                    category AS Category,
                    color AS Color,
                    size AS Size,
                    price AS Price,
                    stock AS Stock,
                    min_stock AS Alert_Level
                FROM products
                ORDER BY id DESC
            """, conn)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.write("")

        if not df.empty:

            selected_id = st.selectbox(
                "Select Product to Edit/Delete",
                df["ID"].tolist()
            )

            product = conn.execute("""
                SELECT *
                FROM products
                WHERE id=?
            """, (selected_id,)).fetchone()

            if product:

                st.markdown("### Edit Product")

                e1, e2, e3 = st.columns(3)

                with e1:

                    edit_name = st.text_input(
                        "Name",
                        value=product["name"] or ""
                    )

                    edit_brand = st.text_input(
                        "Brand",
                        value=product["brand"] or ""
                    )

                    edit_category = st.text_input(
                        "Category",
                        value=product["category"] or ""
                    )

                with e2:

                    edit_color = st.text_input(
                        "Color",
                        value=product["color"] or ""
                    )

                    edit_size = st.text_input(
                        "Size",
                        value=product["size"] or ""
                    )

                    edit_price = st.number_input(
                        "Price",
                        min_value=0.0,
                        value=float(product["price"] or 0),
                        step=100.0
                    )

                with e3:

                    edit_stock = st.number_input(
                        "Stock Quantity",
                        min_value=0,
                        value=int(product["stock"] or 0),
                        step=1
                    )

                    edit_min_stock = st.number_input(
                        "Low Stock Alert",
                        min_value=0,
                        value=int(product["min_stock"] or 5),
                        step=1
                    )

                if st.button(
                    "💾 Save Changes",
                    type="primary"
                ):

                    conn.execute("""
                        UPDATE products
                        SET
                            name=?,
                            brand=?,
                            category=?,
                            color=?,
                            size=?,
                            price=?,
                            stock=?,
                            min_stock=?
                        WHERE id=?
                    """, (
                        edit_name,
                        edit_brand,
                        edit_category,
                        edit_color,
                        edit_size,
                        edit_price,
                        edit_stock,
                        edit_min_stock,
                        selected_id
                    ))

                    conn.commit()

                    st.success("Product updated successfully.")
                    st.rerun()

                st.write("")

                if st.button(
                    "🗑️ Delete Product",
                    type="secondary"
                ):

                    conn.execute(
                        "DELETE FROM products WHERE id=?",
                        (selected_id,)
                    )

                    conn.commit()

                    st.success("Product deleted.")
                    st.rerun()


# =========================================================
# ADMIN SALES HISTORY
# =========================================================

def admin_sales_history():

    if not require_admin():
        return

    st.markdown(
        "<div class='main-title'>Sales History</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='subtitle'>Complete sales record</div>",
        unsafe_allow_html=True
    )

    df = pd.read_sql_query("""
        SELECT
            invoice_no AS Invoice,
            seller AS Seller,
            subtotal AS Subtotal,
            discount AS Discount,
            tax AS Tax,
            total AS Total,
            payment_method AS Payment,
            created_at AS Date
        FROM sales
        ORDER BY id DESC
    """, conn)

    if df.empty:

        st.info("No sales yet.")

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# ADMIN STOCK HISTORY
# =========================================================

def admin_stock_history():

    if not require_admin():
        return

    st.markdown(
        "<div class='main-title'>Stock History</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='subtitle'>All stock additions and sales deductions</div>",
        unsafe_allow_html=True
    )

    df = pd.read_sql_query("""
        SELECT
            sku AS SKU,
            product_name AS Product,
            quantity AS Quantity,
            action AS Action,
            reason AS Reason,
            created_by AS User,
            created_at AS Date
        FROM stock_history
        ORDER BY id DESC
    """, conn)

    if df.empty:

        st.info("No stock history yet.")

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# ADMIN SETTINGS
# =========================================================

def admin_settings():

    if not require_admin():
        return

    st.markdown(
        "<div class='main-title'>Settings</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='subtitle'>Manage POS settings</div>",
        unsafe_allow_html=True
    )

    current_store = get_setting(
        conn,
        "store_name",
        "Shoe Shop POS"
    )

    current_currency = get_setting(
        conn,
        "currency",
        "PKR"
    )

    store = st.text_input(
        "Store Name",
        value=current_store
    )

    currency_value = st.text_input(
        "Currency",
        value=current_currency
    )

    if st.button(
        "💾 Save Settings",
        type="primary"
    ):

        set_setting(
            conn,
            "store_name",
            store
        )

        set_setting(
            conn,
            "currency",
            currency_value
        )

        st.success(
            "Settings saved successfully."
        )

        st.rerun()


# =========================================================
# SELLER SEARCH
# =========================================================

def seller_search_products(search):

    if not search.strip():
        return []

    like = f"%{search.strip()}%"

    rows = conn.execute("""
        SELECT
            id,
            sku,
            name,
            brand,
            category,
            color,
            size,
            price,
            stock
        FROM products
        WHERE
            name LIKE ?
            OR sku LIKE ?
            OR brand LIKE ?
            OR category LIKE ?
            OR color LIKE ?
            OR size LIKE ?
        ORDER BY name
        LIMIT 50
    """, (
        like,
        like,
        like,
        like,
        like,
        like
    )).fetchall()

    return rows


# =========================================================
# ADD TO CART
# =========================================================

def add_to_cart(product_id):

    product = conn.execute("""
        SELECT *
        FROM products
        WHERE id=?
    """, (product_id,)).fetchone()

    if not product:
        st.error("Product not found.")
        return

    if int(product["stock"]) <= 0:
        st.error("This product is out of stock.")
        return

    for item in st.session_state.cart:

        if item["product_id"] == product_id:

            if item["quantity"] >= int(product["stock"]):
                st.warning("Maximum available stock reached.")
                return

            item["quantity"] += 1
            return

    st.session_state.cart.append({
        "product_id": product["id"],
        "name": product["name"],
        "sku": product["sku"],
        "price": float(product["price"]),
        "quantity": 1
    })


# =========================================================
# SELLER POS
# =========================================================

def seller_pos():

    if not require_seller():
        return

    st.markdown(
        "<div class='main-title'>New Sale</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='subtitle'>Search for a product to create a sale</div>",
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    st.markdown(
        "<div class='search-box'>",
        unsafe_allow_html=True
    )

    search = st.text_input(
        "🔎 Search Product",
        placeholder="Type product name, SKU, brand, category, color or size..."
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # NO PRODUCTS SHOWN UNTIL USER SEARCHES
    # -----------------------------------------------------

    if search.strip():

        products = seller_search_products(search)

        if not products:

            st.warning(
                "No product found for this search."
            )

        else:

            st.markdown(
                f"### 🔎 Search Results ({len(products)})"
            )

            for product in products:

                col1, col2, col3 = st.columns(
                    [5, 2, 1]
                )

                with col1:

                    st.markdown(
                        f"""
                        <div class="product-card">
                            <div class="product-name">
                                {product["name"]}
                            </div>

                            <div class="product-info">
                                SKU: {product["sku"]}
                                &nbsp; | &nbsp;
                                Brand: {product["brand"]}
                                &nbsp; | &nbsp;
                                Category: {product["category"]}
                                &nbsp; | &nbsp;
                                Color: {product["color"]}
                                &nbsp; | &nbsp;
                                Size: {product["size"]}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:

                    st.markdown(
                        f"""
                        <div class="product-card">
                            <div class="price">
                                {money(product["price"], currency)}
                            </div>

                            <div class="stock">
                                Stock: {product["stock"]}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col3:

                    st.write("")

                    if st.button(
                        "➕ Add",
                        key=f"add_{product['id']}"
                    ):

                        add_to_cart(
                            product["id"]
                        )

                        st.rerun()

    else:

        st.info(
            "🔎 Search for a product above. "
            "Products will appear here after you search."
        )

    st.divider()

    # =====================================================
    # CART
    # =====================================================

    left, right = st.columns(
        [7, 3]
    )

    with left:

        st.markdown("### 🛒 Current Sale")

        if not st.session_state.cart:

            st.info(
                "Cart is empty. Search for a product and click Add."
            )

        else:

            for index, item in enumerate(
                st.session_state.cart
            ):

                product = conn.execute("""
                    SELECT stock
                    FROM products
                    WHERE id=?
                """, (
                    item["product_id"],
                )).fetchone()

                available_stock = (
                    int(product["stock"])
                    if product else 0
                )

                c1, c2, c3, c4 = st.columns(
                    [4, 2, 2, 1]
                )

                with c1:

                    st.markdown(
                        f"**{item['name']}**  \n"
                        f"SKU: `{item['sku']}`"
                    )

                with c2:

                    st.write(
                        money(
                            item["price"],
                            currency
                        )
                    )

                with c3:

                    new_qty = st.number_input(
                        "Qty",
                        min_value=1,
                        max_value=max(
                            1,
                            available_stock
                        ),
                        value=min(
                            item["quantity"],
                            max(
                                1,
                                available_stock
                            )
                        ),
                        key=f"qty_{index}"
                    )

                    item["quantity"] = new_qty

                with c4:

                    if st.button(
                        "❌",
                        key=f"remove_{index}"
                    ):

                        st.session_state.cart.pop(
                            index
                        )

                        st.rerun()

                st.divider()

    # =====================================================
    # SUMMARY
    # =====================================================

    with right:

        st.markdown(
            "<div class='cart-box'>",
            unsafe_allow_html=True
        )

        st.markdown("### 💰 Sale Summary")

        subtotal = sum(
            item["price"] * item["quantity"]
            for item in st.session_state.cart
        )

        discount = st.number_input(
            "Discount",
            min_value=0.0,
            max_value=float(subtotal),
            value=0.0,
            step=100.0
        )

        tax_percent = st.number_input(
            "Tax %",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=1.0
        )

        taxable = max(
            0,
            subtotal - discount
        )

        tax_amount = (
            taxable *
            tax_percent /
            100
        )

        total = (
            taxable +
            tax_amount
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
            f"""
            **Subtotal:** {money(subtotal, currency)}  
            **Discount:** {money(discount, currency)}  
            **Tax:** {money(tax_amount, currency)}  
            ---
            ### Total: {money(total, currency)}
            """
        )

        if st.button(
            "✅ Complete Sale",
            type="primary",
            use_container_width=True
        ):

            if not st.session_state.cart:

                st.error(
                    "Cart is empty."
                )

            else:

                # -----------------------------------------
                # Recheck stock before completing sale
                # -----------------------------------------

                stock_error = False

                for item in st.session_state.cart:

                    product = conn.execute("""
                        SELECT stock
                        FROM products
                        WHERE id=?
                    """, (
                        item["product_id"],
                    )).fetchone()

                    if not product:

                        st.error(
                            f"{item['name']} no longer exists."
                        )

                        stock_error = True
                        break

                    if (
                        int(product["stock"])
                        < int(item["quantity"])
                    ):

                        st.error(
                            f"Not enough stock for {item['name']}."
                        )

                        stock_error = True
                        break

                if not stock_error:

                    try:

                        # ---------------------------------
                        # START TRANSACTION
                        # ---------------------------------

                        conn.execute("BEGIN")

                        invoice_no = generate_invoice()

                        created_at = datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )

                        # ---------------------------------
                        # SALES
                        # ---------------------------------

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
                            invoice_no,
                            st.session_state.user_name,
                            subtotal,
                            discount,
                            tax_amount,
                            total,
                            payment,
                            created_at
                        ))

                        sale_id = cursor.lastrowid

                        # ---------------------------------
                        # SALE ITEMS + STOCK
                        # ---------------------------------

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

                            # Decrease stock

                            conn.execute("""
                                UPDATE products
                                SET stock = stock - ?
                                WHERE id=?
                            """, (
                                item["quantity"],
                                item["product_id"]
                            ))

                            # Stock history

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
                                invoice_no,
                                st.session_state.user_name,
                                created_at
                            ))

                        # ---------------------------------
                        # COMMIT
                        # ---------------------------------

                        conn.commit()

                        st.session_state.cart = []

                        st.success(
                            f"Sale completed successfully! "
                            f"Invoice: {invoice_no}"
                        )

                        st.rerun()

                    except Exception as e:

                        conn.rollback()

                        st.error(
                            f"Sale could not be completed: {e}"
                        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


# =========================================================
# SIDEBAR
# =========================================================

def sidebar():

    with st.sidebar:

        st.markdown(
            f"""
            <div style='text-align:center;padding:15px;'>
                <div style='font-size:45px;'>👟</div>
                <h2>{store_name}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        if st.session_state.role == "admin":

            st.markdown(
                "<div class='admin-badge'>ADMIN</div>",
                unsafe_allow_html=True
            )

            st.write(
                f"👤 {st.session_state.user_name}"
            )

            st.divider()

            page = st.radio(
                "Admin Menu",
                [
                    "📊 Dashboard",
                    "📦 Inventory",
                    "💰 Sales History",
                    "📋 Stock History",
                    "⚙️ Settings"
                ]
            )

            st.divider()

            if st.button(
                "🚪 Logout",
                use_container_width=True
            ):
                logout()

            return page

        elif st.session_state.role == "seller":

            st.markdown(
                "<div class='seller-badge'>SELLER</div>",
                unsafe_allow_html=True
            )

            st.write(
                f"👤 {st.session_state.user_name}"
            )

            st.divider()

            # ONLY seller option
            page = st.radio(
                "Seller Menu",
                [
                    "🛒 New Sale"
                ]
            )

            st.divider()

            if st.button(
                "🚪 Logout",
                use_container_width=True
            ):
                logout()

            return page


# =========================================================
# MAIN
# =========================================================

if not st.session_state.logged_in:

    login_page()

else:

    selected_page = sidebar()

    # =====================================================
    # ADMIN
    # =====================================================

    if st.session_state.role == "admin":

        if selected_page == "📊 Dashboard":
            admin_dashboard()

        elif selected_page == "📦 Inventory":
            admin_inventory()

        elif selected_page == "💰 Sales History":
            admin_sales_history()

        elif selected_page == "📋 Stock History":
            admin_stock_history()

        elif selected_page == "⚙️ Settings":
            admin_settings()

    # =====================================================
    # SELLER
    # =====================================================

    elif st.session_state.role == "seller":

        if selected_page == "🛒 New Sale":
            seller_pos()
