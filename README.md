# 👟 ShoeShop POS System

A professional **Shoe Shop Point of Sale (POS) System** built with Python and Streamlit.

It provides inventory management, sales processing, dashboard analytics, product search, admin controls, and sales history in one application.

---

## 🚀 Features

### 📊 Advanced Dashboard

* Today's sales
* Total transactions
* Total products
* Total stock units
* Low-stock products
* Inventory value
* Recent sales

### 📦 Inventory Management

* Add products
* Edit products
* Delete products
* Product categories
* Brands
* Sizes
* Colors
* SKU / Barcode field
* Purchase price
* Sale price
* Stock quantity
* Low-stock monitoring
* Inventory search
* CSV export

### 🔎 Smart Product Search

Search products by:

* Product name
* Brand
* Category
* Color
* Size
* SKU

Example:

```text
Nike
Running
Black
SHOE-0025
```

All matching products will appear automatically.

### 🛒 New Sale

* Search products
* Add products to cart
* Increase/decrease quantity
* Automatic subtotal
* Discount
* Tax
* Final total
* Customer name
* Payment method
* Automatic stock deduction
* Automatic invoice number

### 🧾 Sales History

* Invoice number
* Customer
* Subtotal
* Discount
* Tax
* Total
* Payment method
* Seller
* Date and time
* Invoice item details
* CSV export

### ⚙️ Settings

Admin can manage:

* Store name
* Currency
* POS configuration
* Security information

### 🔐 Login System

#### Admin

```text
User: Admin
Password: viki90
```

Admin can access:

* Dashboard
* Sales
* Inventory
* Settings
* Product management

#### Seller

Seller does **not require a password**.

Select:

```text
Seller
```

Enter seller name and enter the POS.

---

## 🗄️ Database

The application uses **SQLite**.

The database file is automatically created:

```text
shoe_shop_pos.db
```

It stores:

* Products
* Inventory
* Sales
* Sale items
* Settings

No separate database server is required.

---

## 📁 Project Structure

```text
ShoeShop-POS/
│
├── app.py
├── requirements.txt
├── README.md
└── shoe_shop_pos.db
```

The database file will be created automatically when the application runs.

---

## 💻 Installation

### 1. Install Python

Install Python 3.x on your computer.

### 2. Install Dependencies

Open Command Prompt in the project folder and run:

```bash
pip install -r requirements.txt
```

### 3. Run the POS

Run:

```bash
streamlit run app.py
```

The application will open in your browser.

---

## 📦 Requirements

The project requires:

```text
streamlit
pandas
```

---

## 🧪 First Login

After opening the application:

### Admin

Select:

```text
Admin
```

Password:

```text
viki90
```

### Seller

Select:

```text
Seller
```

Enter any seller name.

No password is required.

---

## 👟 Default Products

The application automatically creates **100 sample shoe products** on the first run.

Products include different:

* Brands
* Categories
* Colors
* Sizes
* Prices
* Stock quantities
* SKUs

The sample products are generated automatically if the database is empty.

---

## 🔎 Product Search Example

Search:

```text
Adidas
```

The POS displays matching Adidas products.

Search:

```text
Sneakers
```

The POS displays matching sneaker products.

Search:

```text
Black
```

The POS displays matching black shoes.

Search:

```text
SHOE-0010
```

The POS displays the matching SKU.

---

## 💳 Completing a Sale

1. Open **New Sale**
2. Search for a product
3. Click **Add**
4. Adjust quantity
5. Enter customer name
6. Select payment method
7. Add discount if required
8. Add tax if required
9. Click **COMPLETE SALE**

The system will:

```text
Create Invoice
       ↓
Save Sale
       ↓
Save Sale Items
       ↓
Reduce Inventory
       ↓
Show Success
```

---

## 💾 Data Persistence

All important information is stored locally in:

```text
shoe_shop_pos.db
```

Closing or restarting the Streamlit application does not automatically delete the database.

---

## ⚠️ Production Security

The current demo/admin password is:

```text
viki90
```

For a real commercial POS deployment, the authentication system should be upgraded to use:

* Password hashing
* Secure sessions
* Role-based permissions
* Environment variables/secrets
* Audit logs
* Database backups

---

## 🔮 Planned Improvements

Future versions can include:

* 📷 Camera barcode scanner
* 🔳 QR code scanner
* 🖨️ Thermal receipt printing
* 🧾 Professional invoice PDF
* 📈 Advanced profit analytics
* 👥 Customer management
* 🚚 Supplier management
* 💰 Expense management
* 📊 Detailed reports
* 📥 Excel import
* 💾 Automatic backups
* 👤 Multiple seller accounts
* 🔐 Advanced permissions
* 🌙 Dark mode
* 🏪 Multi-branch support
* ☁️ Cloud database
* 📱 Mobile-friendly POS interface

---

## 👨‍💻 Technology

Built with:

* Python
* Streamlit
* SQLite
* Pandas

---

## 📄 License

This project is intended for personal, educational, and commercial POS development purposes.

---

# 👟 ShoeShop POS

**Simple • Professional • Fast • Easy to Manage**
