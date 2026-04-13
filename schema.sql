-- ============================================================
-- Insurance Policy Management System — MySQL Database Schema
-- Engine : InnoDB  |  Charset : utf8mb4
-- ============================================================

DROP DATABASE IF EXISTS insurance_db;
CREATE DATABASE insurance_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE insurance_db;

-- ============================================================
-- 1. CUSTOMERS
-- ============================================================
CREATE TABLE customers (
    id         INT            AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100)   NOT NULL,
    email      VARCHAR(150)   NOT NULL UNIQUE,
    phone      VARCHAR(15)    NOT NULL,
    address    VARCHAR(255)   NOT NULL,
    dob        DATE           NOT NULL,
    created_at TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- 2. POLICIES
-- ============================================================
CREATE TABLE policies (
    id              INT            AUTO_INCREMENT PRIMARY KEY,
    customer_id     INT            NOT NULL,
    policy_number   VARCHAR(20)    NOT NULL UNIQUE,
    policy_type     ENUM('Health','Life','Vehicle','Home','Travel') NOT NULL,
    premium_amount  DECIMAL(12,2)  NOT NULL,
    coverage_amount DECIMAL(14,2)  NOT NULL,
    start_date      DATE           NOT NULL,
    end_date        DATE           NOT NULL,
    status          ENUM('active','expired','cancelled') NOT NULL DEFAULT 'active',

    CONSTRAINT chk_premium_positive  CHECK (premium_amount  > 0),
    CONSTRAINT chk_coverage_positive CHECK (coverage_amount > 0),

    CONSTRAINT fk_policies_customer
        FOREIGN KEY (customer_id) REFERENCES customers(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 3. CLAIMS
-- ============================================================
CREATE TABLE claims (
    id            INT            AUTO_INCREMENT PRIMARY KEY,
    policy_id     INT            NOT NULL,
    claim_date    DATE           NOT NULL,
    description   TEXT           NOT NULL,
    claim_amount  DECIMAL(12,2)  NOT NULL,
    status        ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    resolved_date DATE           NULL,

    CONSTRAINT chk_claim_amount_positive CHECK (claim_amount > 0),

    CONSTRAINT fk_claims_policy
        FOREIGN KEY (policy_id) REFERENCES policies(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 4. PAYMENTS
-- ============================================================
CREATE TABLE payments (
    id             INT            AUTO_INCREMENT PRIMARY KEY,
    policy_id      INT            NOT NULL,
    amount         DECIMAL(12,2)  NOT NULL,
    payment_date   DATE           NOT NULL,
    payment_method ENUM('cash','card','upi','netbanking') NOT NULL,

    CONSTRAINT chk_payment_amount_positive CHECK (amount > 0),

    CONSTRAINT fk_payments_policy
        FOREIGN KEY (policy_id) REFERENCES policies(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 5. VIEW — active_policies_view
-- ============================================================
CREATE OR REPLACE VIEW active_policies_view AS
SELECT
    c.id            AS customer_id,
    c.name          AS customer_name,
    c.email         AS customer_email,
    c.phone         AS customer_phone,
    p.id            AS policy_id,
    p.policy_number,
    p.policy_type,
    p.premium_amount,
    p.coverage_amount,
    p.start_date,
    p.end_date,
    p.status        AS policy_status
FROM customers c
JOIN policies p ON c.id = p.customer_id
WHERE p.status = 'active';

-- ============================================================
-- 6. STORED PROCEDURE — approve_claim
--    • Sets claim status → 'approved'
--    • Sets resolved_date → CURDATE()
--    • Inserts a payment record for the claim amount
--    • Wrapped in a TRANSACTION with error handling
-- ============================================================
DELIMITER //

CREATE PROCEDURE approve_claim(IN p_claim_id INT)
BEGIN
    DECLARE v_policy_id    INT;
    DECLARE v_claim_amount DECIMAL(12,2);

    -- Error handler: rollback on any SQL exception
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Could not approve claim. Transaction rolled back.';
    END;

    START TRANSACTION;

    -- Fetch claim details (lock the row for update)
    SELECT policy_id, claim_amount
    INTO   v_policy_id, v_claim_amount
    FROM   claims
    WHERE  id = p_claim_id
    FOR UPDATE;

    -- Update claim status
    UPDATE claims
    SET    status        = 'approved',
           resolved_date = CURDATE()
    WHERE  id = p_claim_id;

    -- Insert corresponding payment record
    INSERT INTO payments (policy_id, amount, payment_date, payment_method)
    VALUES (v_policy_id, v_claim_amount, CURDATE(), 'netbanking');

    COMMIT;
END //

DELIMITER ;

-- ============================================================
-- 7. DEMO DATA — Realistic Indian Entries
-- ============================================================

-- 7a. Customers (10 rows)
INSERT INTO customers (name, email, phone, address, dob) VALUES
('Aarav Sharma',    'aarav.sharma@gmail.com',    '9876543210', '12, MG Road, Bengaluru, Karnataka 560001',        '1990-05-14'),
('Priya Verma',     'priya.verma@yahoo.com',     '9123456780', '45, Civil Lines, Lucknow, Uttar Pradesh 226001',  '1985-11-22'),
('Rohan Mehta',     'rohan.mehta@outlook.com',    '9988776655', '78, FC Road, Pune, Maharashtra 411004',           '1992-03-08'),
('Sneha Iyer',      'sneha.iyer@gmail.com',      '9871234560', '23, Anna Nagar, Chennai, Tamil Nadu 600040',      '1988-07-30'),
('Vikram Singh',    'vikram.singh@hotmail.com',   '9765432100', '9, Sector 17, Chandigarh 160017',                 '1995-01-19'),
('Ananya Reddy',    'ananya.reddy@gmail.com',     '9654321098', '56, Jubilee Hills, Hyderabad, Telangana 500033',  '1993-09-12'),
('Karan Patel',     'karan.patel@yahoo.com',      '9543210987', '101, SG Highway, Ahmedabad, Gujarat 380054',     '1987-12-05'),
('Meera Nair',      'meera.nair@gmail.com',       '9432109876', '34, Marine Drive, Kochi, Kerala 682031',          '1991-06-25'),
('Arjun Gupta',     'arjun.gupta@outlook.com',    '9321098765', '67, Park Street, Kolkata, West Bengal 700016',    '1989-02-17'),
('Divya Joshi',     'divya.joshi@gmail.com',      '9210987654', '22, Malviya Nagar, Jaipur, Rajasthan 302017',    '1994-10-03');

-- 7b. Policies (10 rows)
INSERT INTO policies (customer_id, policy_number, policy_type, premium_amount, coverage_amount, start_date, end_date, status) VALUES
(1,  'POL-2024-1001', 'Health',  12000.00,  500000.00,  '2024-01-15', '2025-01-14', 'active'),
(2,  'POL-2024-1002', 'Life',    18000.00, 2000000.00,  '2024-03-01', '2044-02-28', 'active'),
(3,  'POL-2024-1003', 'Vehicle',  8500.00,  300000.00,  '2024-06-10', '2025-06-09', 'active'),
(4,  'POL-2024-1004', 'Home',    15000.00, 1500000.00,  '2024-02-20', '2025-02-19', 'active'),
(5,  'POL-2024-1005', 'Travel',   3500.00,  200000.00,  '2024-07-01', '2024-07-15', 'expired'),
(6,  'POL-2024-1006', 'Health',  14000.00,  750000.00,  '2024-04-05', '2025-04-04', 'active'),
(7,  'POL-2024-1007', 'Vehicle',  9200.00,  400000.00,  '2024-05-18', '2025-05-17', 'active'),
(8,  'POL-2024-1008', 'Life',    22000.00, 2500000.00,  '2024-01-01', '2044-12-31', 'active'),
(9,  'POL-2024-1009', 'Home',    11000.00, 1000000.00,  '2023-08-15', '2024-08-14', 'expired'),
(10, 'POL-2024-1010', 'Health',  13000.00,  600000.00,  '2024-09-01', '2025-08-31', 'active');

-- 7c. Claims (10 rows)
INSERT INTO claims (policy_id, claim_date, description, claim_amount, status, resolved_date) VALUES
(1,  '2024-06-10', 'Hospitalisation for dengue fever at Apollo Hospital, Bengaluru',          45000.00,  'approved',  '2024-06-20'),
(2,  '2024-08-15', 'Critical illness diagnosis — cardiac treatment at Medanta, Lucknow',     150000.00, 'pending',   NULL),
(3,  '2024-09-02', 'Two-wheeler accident damage repair at authorised service centre, Pune',    28000.00,  'approved',  '2024-09-12'),
(4,  '2024-07-25', 'Water damage to ground floor due to heavy monsoon flooding, Chennai',    120000.00, 'pending',   NULL),
(6,  '2024-10-11', 'Knee replacement surgery at KIMS Hospital, Hyderabad',                   200000.00, 'approved',  '2024-10-25'),
(7,  '2024-11-03', 'Car windshield damage from hailstorm in Ahmedabad',                       35000.00,  'rejected',  '2024-11-10'),
(8,  '2024-05-20', 'Accidental death benefit claim processing for nominee, Kochi',           500000.00, 'pending',   NULL),
(10, '2025-01-05', 'Emergency appendectomy at SMS Hospital, Jaipur',                          60000.00,  'approved',  '2025-01-15'),
(1,  '2025-02-14', 'Outpatient treatment for fracture at Manipal Hospital, Bengaluru',        18000.00,  'pending',   NULL),
(3,  '2025-03-01', 'Theft of two-wheeler — FIR filed, claim for insured value, Pune',        150000.00, 'pending',   NULL);

-- 7d. Payments (10 rows)
INSERT INTO payments (policy_id, amount, payment_date, payment_method) VALUES
(1,  12000.00, '2024-01-15', 'upi'),
(2,  18000.00, '2024-03-01', 'netbanking'),
(3,   8500.00, '2024-06-10', 'card'),
(4,  15000.00, '2024-02-20', 'netbanking'),
(5,   3500.00, '2024-07-01', 'upi'),
(6,  14000.00, '2024-04-05', 'card'),
(7,   9200.00, '2024-05-18', 'cash'),
(8,  22000.00, '2024-01-01', 'netbanking'),
(9,  11000.00, '2023-08-15', 'upi'),
(10, 13000.00, '2024-09-01', 'card');

-- ============================================================
-- Done! Run this file with:
--   mysql -u root -p < schema.sql
-- ============================================================
