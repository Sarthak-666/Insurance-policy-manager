#  Insurance Policy Management System

A full-stack admin portal for managing insurance customers, policies, claims, and payments — built with Flask and MySQL.

---

## 📋 Overview

This is an admin-facing web application that allows an insurance company to manage its core operations from a single dashboard. The system tracks customers, their associated policies, claims raised against those policies, and premium payment records.

---

## ✨ Features

### Dashboard
- Summary statistics — total customers, total policies, active policies, pending claims
- Total premium collected across all payments
- Recent 5 policies with customer names

### Customer Management
- Add, edit, and delete customers
- Search customers by name
- Stores name, email, phone, address, and date of birth

### Policy Management
- Add and edit policies linked to customers
- Supports 5 policy types: Health, Life, Vehicle, Home, Travel
- Tracks premium amount, coverage amount, start/end dates, and status (active / expired / cancelled)

### Claims Management
- Submit claims against existing policies
- Approve or reject claims
- Claim approval is handled atomically — approving a claim automatically creates a corresponding payment record in the same database transaction
- Tracks claim date, description, claim amount, status, and resolution date

### Payments
- Full payment history with policy and customer details
- Supports payment methods: Cash, Card, UPI, Net Banking
- Displays total premium collected

---

## 🗄️ Database Schema

Designed and implemented in MySQL with InnoDB engine, referential integrity via foreign keys, and CHECK constraints on all monetary fields.

```
customers
    └── policies (FK: customer_id → customers.id, CASCADE DELETE)
            └── claims   (FK: policy_id  → policies.id, CASCADE DELETE)
            └── payments (FK: policy_id  → policies.id, CASCADE DELETE)
```

| Table | Description |
|---|---|
| `customers` | Policyholder personal details |
| `policies` | Insurance policies linked to customers |
| `claims` | Claims raised against policies |
| `payments` | Premium payment records |

### Additional Database Objects
- **View:** `active_policies_view` — joins customers and policies, filters only active policies
- **Stored Procedure:** `approve_claim(claim_id)` — atomically approves a claim and inserts a payment record within a transaction with rollback on error

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | MySQL 8.x, MySQL Workbench |
| Frontend | HTML, Bootstrap 5 |
| DB Connector | mysql-connector-python |

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.8+
- MySQL Server 8.x running on localhost
- pip

### 1. Clone the repository
```bash
git clone https://github.com/Sarthak-666/insurance-policy-manager.git
cd insurance-policy-manager
```

### 2. Install dependencies
```bash
pip install flask mysql-connector-python python-dotenv
```

### 3. Configure environment variables
Create a `.env` file in the project root:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_PORT=3306
```

### 4. Initialize the database
```bash
python init_db.py
```
This will:
- Create the `insurance_db` database
- Create all tables, views, and stored procedures
- Populate demo data (10 customers, 10 policies, 10 claims, 10 payments)

### 5. Run the application
```bash
python app.py
```

Open your browser and navigate to: **http://localhost:5000**

---

## 📁 Project Structure

```
insurance-policy-manager/
├── app.py              # Flask application — routes and business logic
├── schema.sql          # MySQL schema — tables, views, stored procedure, demo data
├── init_db.py          # Database initialisation script
├── templates/          # HTML templates (Jinja2)
│   ├── dashboard.html
│   ├── customers.html
│   ├── customer_form.html
│   ├── policies.html
│   ├── policy_form.html
│   ├── claims.html
│   ├── claim_form.html
│   ├── payments.html
│   └── 404.html
├── .env.example        # Environment variable template
├── .gitignore
└── README.md
```

---

## 🔒 Security Notes

- Database credentials are managed via environment variables (`.env`) and never hardcoded
- `.env` is excluded from version control via `.gitignore`
- All database queries use parameterized statements to prevent SQL injection

---

## 👨‍💻 Author

**Sarthak Maganty**  
B.Tech, Computer and Communication Engineering  
Manipal University Jaipur  
[GitHub](https://github.com/Sarthak-666) · [LinkedIn](https://www.linkedin.com/in/sarthak-maganty-bb0b59272/)
