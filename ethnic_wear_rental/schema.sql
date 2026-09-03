-- ============================================================
--  Ethnic Wear Rental Shop - Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS ethnic_wear_rental
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE ethnic_wear_rental;

-- ------------------------------------------------------------
--  CATEGORIES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100)  NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
--  INVENTORY ITEMS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(200)    NOT NULL,
    category_id     INT             NOT NULL,
    size            VARCHAR(20)     NOT NULL,          -- XS, S, M, L, XL, XXL, Free Size
    color           VARCHAR(80)     NOT NULL,
    fabric          VARCHAR(100),
    occasion        VARCHAR(100),                      -- Wedding, Festival, Party, etc.
    rental_price    DECIMAL(10,2)   NOT NULL,
    deposit_amount  DECIMAL(10,2)   DEFAULT 0.00,
    quantity_total  INT             NOT NULL DEFAULT 1,
    quantity_available INT          NOT NULL DEFAULT 1,
    condition_status ENUM('Excellent','Good','Fair','Needs Repair') DEFAULT 'Excellent',
    description     TEXT,
    image_url       VARCHAR(500),
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
);

-- ------------------------------------------------------------
--  CUSTOMERS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150)    NOT NULL,
    phone           VARCHAR(20)     NOT NULL UNIQUE,
    email           VARCHAR(150),
    address         TEXT,
    id_proof_type   ENUM('Aadhar','PAN','Passport','Voter ID','Driving Licence') DEFAULT 'Aadhar',
    id_proof_number VARCHAR(50),
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
--  RENTALS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rentals (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    rental_code     VARCHAR(30)     NOT NULL UNIQUE,
    customer_id     INT             NOT NULL,
    rental_date     DATE            NOT NULL,
    return_due_date DATE            NOT NULL,
    actual_return_date DATE,
    total_amount    DECIMAL(10,2)   NOT NULL DEFAULT 0.00,
    deposit_paid    DECIMAL(10,2)   NOT NULL DEFAULT 0.00,
    late_fee        DECIMAL(10,2)   DEFAULT 0.00,
    status          ENUM('Active','Returned','Overdue','Cancelled') DEFAULT 'Active',
    notes           TEXT,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT
);

-- ------------------------------------------------------------
--  RENTAL ITEMS  (line items per rental)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rental_items (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    rental_id       INT             NOT NULL,
    inventory_id    INT             NOT NULL,
    quantity        INT             NOT NULL DEFAULT 1,
    unit_price      DECIMAL(10,2)   NOT NULL,
    FOREIGN KEY (rental_id)    REFERENCES rentals(id)   ON DELETE CASCADE,
    FOREIGN KEY (inventory_id) REFERENCES inventory(id) ON DELETE RESTRICT
);

-- ============================================================
--  SEED DATA
-- ============================================================

-- Categories
INSERT IGNORE INTO categories (name, description) VALUES
    ('Saree',          'Traditional Indian drape worn by women'),
    ('Lehenga',        'Flared skirt set worn at weddings and festivals'),
    ('Salwar Kameez',  'Tunic with trousers, versatile ethnic wear'),
    ('Sherwani',       'Long coat-like garment for grooms and formal occasions'),
    ('Kurta Pajama',   'Casual to semi-formal ethnic set for men'),
    ('Anarkali',       'Long flared kurta suit for women'),
    ('Dhoti Kurta',    'Traditional male attire for rituals and weddings'),
    ('Ghagra Choli',   'Rajasthani/Gujarati skirt-blouse set'),
    ('Indo Western',   'Fusion of traditional and western styles'),
    ('Accessories',    'Jewellery, dupattas, turbans, and more');

-- Sample Inventory
INSERT IGNORE INTO inventory
    (name, category_id, size, color, fabric, occasion, rental_price, deposit_amount, quantity_total, quantity_available, condition_status, description)
VALUES
    ('Banarasi Silk Saree - Gold',          1, 'Free Size', 'Gold & Red',   'Banarasi Silk',  'Wedding',  800.00,  2000.00, 3, 3, 'Excellent', 'Heavy zari work Banarasi saree, perfect for bridal occasions'),
    ('Kanjivaram Silk Saree - Emerald',     1, 'Free Size', 'Emerald Green','Kanjivaram Silk','Wedding',  900.00,  2500.00, 2, 2, 'Excellent', 'Premium Kanjivaram with temple border design'),
    ('Chikankari Saree - Ivory',            1, 'Free Size', 'Ivory White',  'Georgette',      'Festival', 500.00,  1000.00, 4, 4, 'Good',      'Delicate hand-embroidered Lucknowi Chikankari'),
    ('Bridal Lehenga - Crimson',            2, 'M',         'Crimson Red',  'Silk Velvet',    'Wedding', 2500.00,  5000.00, 2, 2, 'Excellent', 'Heavy embroidered bridal lehenga with dupatta'),
    ('Floral Lehenga - Pink',               2, 'S',         'Pastel Pink',  'Net',            'Party',    900.00,  2000.00, 3, 3, 'Good',      'Light floral net lehenga, ideal for sangeet'),
    ('Bandhani Lehenga - Yellow',           2, 'L',         'Yellow',       'Cotton Silk',    'Festival', 700.00,  1500.00, 2, 2, 'Good',      'Vibrant Bandhani print lehenga from Rajasthan'),
    ('Anarkali Suit - Royal Blue',          3, 'M',         'Royal Blue',   'Georgette',      'Party',    600.00,  1200.00, 4, 4, 'Excellent', 'Floor-length Anarkali with churidar'),
    ('Patiala Salwar Kameez - Orange',      3, 'L',         'Orange',       'Cotton',         'Casual',   350.00,   700.00, 5, 5, 'Good',      'Comfortable Patiala suit, perfect for festivals'),
    ('Groom Sherwani - Ivory Gold',         4, 'L',         'Ivory & Gold', 'Brocade',        'Wedding', 3000.00,  6000.00, 2, 2, 'Excellent', 'Premium groom sherwani with intricate gold embroidery'),
    ('Jodhpuri Sherwani - Navy',            4, 'M',         'Navy Blue',    'Wool Blend',     'Wedding', 2000.00,  4000.00, 2, 2, 'Excellent', 'Classic Jodhpuri bandhgala sherwani'),
    ('Kurta Pajama - Mint Green',           5, 'XL',        'Mint Green',   'Cotton',         'Festival', 400.00,   800.00, 6, 6, 'Good',      'Embroidered kurta with straight pajama'),
    ('Silk Kurta Pajama - Maroon',          5, 'L',         'Maroon',       'Pure Silk',      'Wedding',  800.00,  1500.00, 3, 3, 'Excellent', 'Luxurious silk kurta for wedding receptions'),
    ('Ghagra Choli - Mirror Work',          8, 'M',         'Multicolor',   'Cotton Silk',    'Festival', 750.00,  1500.00, 3, 3, 'Good',      'Traditional mirror-work Rajasthani ghagra choli'),
    ('Indo Western Sherwani - Grey',        9, 'M',         'Charcoal Grey','Polyester Blend','Party',   1200.00,  2500.00, 2, 2, 'Excellent', 'Modern Indo-western sherwani with slim fit'),
    ('Dhoti Kurta - White Gold',            7, 'Free Size', 'White & Gold', 'Cotton Silk',    'Wedding',  600.00,  1200.00, 4, 4, 'Good',      'Traditional South Indian dhoti with kurta');

-- Sample Customers
INSERT IGNORE INTO customers (name, phone, email, address, id_proof_type, id_proof_number) VALUES
    ('Priya Sharma',    '9876543210', 'priya.sharma@email.com',   '12, Rose Lane, Mumbai',        'Aadhar', 'XXXX-XXXX-1234'),
    ('Rohan Mehta',     '9823456780', 'rohan.mehta@email.com',    '45, Shivaji Nagar, Pune',      'PAN',    'ABCDE1234F'),
    ('Ananya Verma',    '9712345678', 'ananya.v@email.com',       '7, Green Park, Delhi',         'Aadhar', 'XXXX-XXXX-5678'),
    ('Vikram Singh',    '9654321098', 'vikram.s@email.com',       '22, MG Road, Bangalore',       'Passport','P1234567'),
    ('Deepika Patel',   '9543210987', 'deepika.p@email.com',      '89, Navrangpura, Ahmedabad',   'Voter ID','ABC1234567');
