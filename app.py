"""
Insurance Policy Management System — Flask Application (MySQL version)
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
from datetime import date

# ── App Configuration ────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'insurance_mgmt_secret_key_2024'

# ── MySQL Configuration ─────────────────────────────────────
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'sarthak',
    'database': 'insurance_db',
    'port': 3306,
}


def get_db_connection():
    """Return a new MySQL database connection with dictionary cursor."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"MySQL Connection Error: {e}")
        raise


def db_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    """
    Helper to run a query and return results as list of dicts.
    Handles opening/closing connection and cursor automatically.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if commit:
            conn.commit()
            return cursor
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
        return cursor
    except Exception:
        if commit:
            conn.rollback()
        raise
    finally:
        if not commit:
            cursor.close()
            conn.close()


# ═════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═════════════════════════════════════════════════════════════

@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 page."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """Custom 500 page."""
    flash('An unexpected server error occurred. Please try again.', 'danger')
    return redirect(url_for('dashboard'))


# ═════════════════════════════════════════════════════════════
# 1. DASHBOARD
# ═════════════════════════════════════════════════════════════

@app.route('/')
def dashboard():
    """Display summary cards with aggregate statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Total customers
        cursor.execute("SELECT COUNT(*) AS total FROM customers")
        total_customers = cursor.fetchone()['total']

        # Total policies
        cursor.execute("SELECT COUNT(*) AS total FROM policies")
        total_policies = cursor.fetchone()['total']

        # Active policies
        cursor.execute("SELECT COUNT(*) AS total FROM policies WHERE status = 'active'")
        active_policies = cursor.fetchone()['total']

        # Pending claims
        cursor.execute("SELECT COUNT(*) AS total FROM claims WHERE status = 'pending'")
        pending_claims = cursor.fetchone()['total']

        # Total premium collected (sum of all payments)
        cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM payments")
        total_premium = cursor.fetchone()['total']

        # Recent 5 policies
        cursor.execute("""
            SELECT p.*, c.name AS customer_name
            FROM policies p
            JOIN customers c ON p.customer_id = c.id
            ORDER BY p.id DESC
            LIMIT 5
        """)
        recent_policies = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('dashboard.html',
                               total_customers=total_customers,
                               total_policies=total_policies,
                               active_policies=active_policies,
                               pending_claims=pending_claims,
                               total_premium=total_premium,
                               recent_policies=recent_policies)
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
        return render_template('dashboard.html',
                               total_customers=0,
                               total_policies=0,
                               active_policies=0,
                               pending_claims=0,
                               total_premium=0,
                               recent_policies=[])


# ═════════════════════════════════════════════════════════════
# 2. CUSTOMERS — Full CRUD + Search
# ═════════════════════════════════════════════════════════════

@app.route('/customers')
def list_customers():
    """List all customers, optionally filtered by name."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        search_query = request.args.get('q', '').strip()

        if search_query:
            cursor.execute(
                "SELECT * FROM customers WHERE name LIKE %s ORDER BY id",
                (f'%{search_query}%',)
            )
        else:
            cursor.execute("SELECT * FROM customers ORDER BY id")

        customers = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('customers.html', customers=customers, search_query=search_query)
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
        return render_template('customers.html', customers=[], search_query='')


@app.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    """Show add-customer form (GET) or insert a new customer (POST)."""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO customers (name, email, phone, address, dob) VALUES (%s, %s, %s, %s, %s)",
                (request.form['name'], request.form['email'], request.form['phone'],
                 request.form['address'], request.form['dob'])
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Customer added successfully!', 'success')
            return redirect(url_for('list_customers'))
        except Exception as e:
            flash(f'Error adding customer: {e}', 'danger')
            return redirect(url_for('add_customer'))

    return render_template('customer_form.html')


@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
def edit_customer(id):
    """Show edit form pre-filled (GET) or update customer (POST)."""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE customers SET name=%s, email=%s, phone=%s, address=%s, dob=%s WHERE id=%s",
                (request.form['name'], request.form['email'], request.form['phone'],
                 request.form['address'], request.form['dob'], id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Customer updated successfully!', 'success')
            return redirect(url_for('list_customers'))
        except Exception as e:
            flash(f'Error updating customer: {e}', 'danger')
            return redirect(url_for('edit_customer', id=id))

    # GET — fetch existing customer
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customers WHERE id = %s", (id,))
        customer = cursor.fetchone()
        cursor.close()
        conn.close()
        if not customer:
            flash('Customer not found.', 'warning')
            return redirect(url_for('list_customers'))
        return render_template('customer_form.html', customer=customer)
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
        return redirect(url_for('list_customers'))


@app.route('/customers/delete/<int:id>')
def delete_customer(id):
    """Delete a customer by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customers WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Customer deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting customer: {e}', 'danger')
    return redirect(url_for('list_customers'))


# ═════════════════════════════════════════════════════════════
# 3. POLICIES — CRUD
# ═════════════════════════════════════════════════════════════

@app.route('/policies')
def list_policies():
    """List all policies with customer name via JOIN."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, c.name AS customer_name
            FROM policies p
            JOIN customers c ON p.customer_id = c.id
            ORDER BY p.id
        """)
        policies = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('policies.html', policies=policies)
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
        return render_template('policies.html', policies=[])


@app.route('/policies/add', methods=['GET', 'POST'])
def add_policy():
    """Show add-policy form with customer dropdown (GET) or insert (POST)."""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO policies (customer_id, policy_number, policy_type, "
                "premium_amount, coverage_amount, start_date, end_date, status) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (request.form['customer_id'], request.form['policy_number'],
                 request.form['policy_type'], request.form['premium_amount'],
                 request.form['coverage_amount'], request.form['start_date'],
                 request.form['end_date'], request.form['status'])
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Policy added successfully!', 'success')
            return redirect(url_for('list_policies'))
        except Exception as e:
            flash(f'Error adding policy: {e}', 'danger')
            return redirect(url_for('add_policy'))

    # GET — fetch customers for dropdown
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM customers ORDER BY name")
        customers = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('policy_form.html', customers=customers)
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
        return render_template('policy_form.html', customers=[])


@app.route('/policies/edit/<int:id>', methods=['GET', 'POST'])
def edit_policy(id):
    """Show edit form (GET) or update policy (POST)."""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE policies SET customer_id=%s, policy_number=%s, policy_type=%s, "
                "premium_amount=%s, coverage_amount=%s, start_date=%s, end_date=%s, status=%s "
                "WHERE id=%s",
                (request.form['customer_id'], request.form['policy_number'],
                 request.form['policy_type'], request.form['premium_amount'],
                 request.form['coverage_amount'], request.form['start_date'],
                 request.form['end_date'], request.form['status'], id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Policy updated successfully!', 'success')
            return redirect(url_for('list_policies'))
        except Exception as e:
            flash(f'Error updating policy: {e}', 'danger')
            return redirect(url_for('edit_policy', id=id))

    # GET — fetch policy + customers
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM policies WHERE id = %s", (id,))
        policy = cursor.fetchone()
        cursor.execute("SELECT id, name FROM customers ORDER BY name")
        customers = cursor.fetchall()
        cursor.close()
        conn.close()
        if not policy:
            flash('Policy not found.', 'warning')
            return redirect(url_for('list_policies'))
        return render_template('policy_form.html', policy=policy, customers=customers)
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
        return redirect(url_for('list_policies'))


# ═════════════════════════════════════════════════════════════
# 4. CLAIMS
# ═════════════════════════════════════════════════════════════

@app.route('/claims')
def list_claims():
    """List all claims with policy number and customer name."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT cl.*, p.policy_number, c.name AS customer_name
            FROM claims cl
            JOIN policies p ON cl.policy_id = p.id
            JOIN customers c ON p.customer_id = c.id
            ORDER BY cl.id
        """)
        claims = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('claims.html', claims=claims)
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
        return render_template('claims.html', claims=[])


@app.route('/claims/add', methods=['GET', 'POST'])
def add_claim():
    """Show add-claim form with policy dropdown (GET) or insert (POST)."""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO claims (policy_id, claim_date, description, claim_amount) "
                "VALUES (%s, %s, %s, %s)",
                (request.form['policy_id'], request.form['claim_date'],
                 request.form['description'], request.form['claim_amount'])
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Claim submitted successfully!', 'success')
            return redirect(url_for('list_claims'))
        except Exception as e:
            flash(f'Error adding claim: {e}', 'danger')
            return redirect(url_for('add_claim'))

    # GET — fetch policies for dropdown
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.id, p.policy_number, c.name AS customer_name
            FROM policies p
            JOIN customers c ON p.customer_id = c.id
            ORDER BY p.policy_number
        """)
        policies = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('claim_form.html', policies=policies)
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
        return render_template('claim_form.html', policies=[])


@app.route('/claims/approve/<int:id>', methods=['POST'])
def approve_claim(id):
    """Approve a claim: update status, set resolved_date, insert payment (in a transaction)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch claim details
        cursor.execute("SELECT policy_id, claim_amount FROM claims WHERE id = %s", (id,))
        claim = cursor.fetchone()
        if not claim:
            flash('Claim not found.', 'warning')
            cursor.close()
            conn.close()
            return redirect(url_for('list_claims'))

        today = date.today().isoformat()

        # Use transaction (auto-started by MySQL connector)
        conn.start_transaction()

        # Update claim status
        cursor.execute(
            "UPDATE claims SET status = 'approved', resolved_date = %s WHERE id = %s",
            (today, id)
        )
        # Insert corresponding payment record
        cursor.execute(
            "INSERT INTO payments (policy_id, amount, payment_date, payment_method) VALUES (%s, %s, %s, %s)",
            (claim['policy_id'], claim['claim_amount'], today, 'netbanking')
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Claim approved successfully! Payment record created.', 'success')
    except Exception as e:
        flash(f'Error approving claim: {e}', 'danger')
    return redirect(url_for('list_claims'))


@app.route('/claims/reject/<int:id>', methods=['POST'])
def reject_claim(id):
    """Reject a claim — update status and set resolved_date."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        today = date.today().isoformat()
        cursor.execute(
            "UPDATE claims SET status = 'rejected', resolved_date = %s WHERE id = %s",
            (today, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Claim rejected.', 'warning')
    except Exception as e:
        flash(f'Error rejecting claim: {e}', 'danger')
    return redirect(url_for('list_claims'))


# ═════════════════════════════════════════════════════════════
# 5. PAYMENTS
# ═════════════════════════════════════════════════════════════

@app.route('/payments')
def list_payments():
    """List all payments with policy and customer info."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT pay.*, p.policy_number, c.name AS customer_name
            FROM payments pay
            JOIN policies p ON pay.policy_id = p.id
            JOIN customers c ON p.customer_id = c.id
            ORDER BY pay.payment_date DESC
        """)
        payments = cursor.fetchall()

        # Compute total server-side
        total_amount = sum(float(row['amount']) for row in payments)

        cursor.close()
        conn.close()
        return render_template('payments.html', payments=payments, total_amount=total_amount)
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
        return render_template('payments.html', payments=[], total_amount=0)


# ═════════════════════════════════════════════════════════════
# Run the application
# ═════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app.run(debug=True, port=5000)
