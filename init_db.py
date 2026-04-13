"""
Initialize the MySQL database with schema and demo data.
Run this once: python init_db.py

This script executes schema.sql against MySQL Server using multi_statements.
"""

import mysql.connector
from mysql.connector import Error
import os

# ── MySQL Connection Config ──────────────────────────────────
DB_CONFIG_NO_DB = {
    'host': 'localhost',
    'user': 'root',
    'password': 'sarthak',
    'port': 3306,
}

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')


def init_database():
    """Drop and recreate the insurance_db database from schema.sql."""
    try:
        # Read the schema file
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # ── Parse out DELIMITER blocks (stored procedure) ─────
        lines = schema_sql.split('\n')
        regular_lines = []
        proc_lines = []
        in_delimiter = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('DELIMITER //'):
                in_delimiter = True
                continue
            elif stripped == 'DELIMITER ;':
                in_delimiter = False
                continue
            elif in_delimiter:
                proc_lines.append(line)
            else:
                regular_lines.append(line)

        regular_sql = '\n'.join(regular_lines)

        # ── Step 1: Create DB and tables ──────────────────────
        # Connect WITHOUT a specific database first
        conn = mysql.connector.connect(**DB_CONFIG_NO_DB)
        cursor = conn.cursor()

        # Drop and create database
        cursor.execute("DROP DATABASE IF EXISTS insurance_db")
        cursor.execute("CREATE DATABASE insurance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✅ Database 'insurance_db' created.")
        cursor.close()
        conn.close()

        # ── Step 2: Connect TO the new database and run schema ─
        db_config = {**DB_CONFIG_NO_DB, 'database': 'insurance_db'}
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Split by semicolons and execute each statement
        # Filter out DROP/CREATE DATABASE and USE statements (already handled)
        statements = regular_sql.split(';')
        skip_prefixes = ('DROP DATABASE', 'CREATE DATABASE', 'USE ')

        executed = 0
        for stmt in statements:
            stmt = stmt.strip()
            # Remove comment-only lines
            clean_lines = [l for l in stmt.split('\n') if not l.strip().startswith('--')]
            clean_stmt = '\n'.join(clean_lines).strip()

            if not clean_stmt:
                continue

            # Skip DB-level statements we already ran
            upper = clean_stmt.upper().lstrip()
            if any(upper.startswith(p) for p in skip_prefixes):
                continue

            try:
                cursor.execute(clean_stmt)
                conn.commit()
                executed += 1
            except Error as e:
                print(f"  ⚠ Statement error: {e}")
                print(f"    Statement: {clean_stmt[:80]}...")

        print(f"✅ Executed {executed} SQL statements (tables, views, data).")

        # ── Step 3: Create stored procedure ───────────────────
        if proc_lines:
            proc_sql = '\n'.join(proc_lines).strip()
            if proc_sql.endswith('//'):
                proc_sql = proc_sql[:-2].strip()
            try:
                cursor.execute(proc_sql)
                conn.commit()
                print("✅ Stored procedure 'approve_claim' created.")
            except Error as e:
                print(f"  ⚠ Procedure error: {e}")

        # ── Step 4: Verify ────────────────────────────────────
        cursor.execute("SELECT COUNT(*) FROM customers")
        cust_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM policies")
        pol_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM claims")
        claim_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM payments")
        pay_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        print(f"\n📊 Data verification:")
        print(f"   Customers : {cust_count}")
        print(f"   Policies  : {pol_count}")
        print(f"   Claims    : {claim_count}")
        print(f"   Payments  : {pay_count}")
        print(f"\n🎉 Done! Open MySQL Workbench → connect to localhost → use 'insurance_db'")

    except Error as e:
        print(f"\n❌ MySQL Error: {e}")
        print("\nMake sure:")
        print("  1. MySQL Server is running (check services.msc)")
        print("  2. The root password is correct")
        print("  3. MySQL is listening on port 3306")
        raise


if __name__ == '__main__':
    init_database()
