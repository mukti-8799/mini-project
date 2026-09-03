"""
Padmavati Novelty Stores — Dummy Data Loader
=============================================
Run anytime to wipe and reload a full set of sample data:

    python dummy_data.py

What it loads
-------------
  10  categories
  35  inventory items  (sarees, lehengas, sherwanis, kurtas, etc.)
  15  customers        (name, phone, email, address, ID proof)
  25  rentals          (10 returned, 7 active, 3 overdue, 3 cancelled, 2 partial)
       • Returned rentals have rental_items.returned_at set correctly
       • Partial rentals: 1 item returned, 1 still out (rental stays Active)
       • Overdue rentals have late_fee calculated
"""

import os
from datetime import date, timedelta
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "ethnic_wear_rental"),
    "charset":  "utf8mb4",
}

# ──────────────────────────────────────────────────────────────
#  MASTER DATA
# ──────────────────────────────────────────────────────────────

CATEGORIES = [
    (1,  "Saree",         "Traditional Indian drape worn by women"),
    (2,  "Lehenga",       "Flared skirt set worn at weddings and festivals"),
    (3,  "Salwar Kameez", "Tunic with trousers, versatile ethnic wear"),
    (4,  "Sherwani",      "Long coat-like garment for grooms and formal occasions"),
    (5,  "Kurta Pajama",  "Casual to semi-formal ethnic set for men"),
    (6,  "Anarkali",      "Long flared kurta suit for women"),
    (7,  "Dhoti Kurta",   "Traditional male attire for rituals and weddings"),
    (8,  "Ghagra Choli",  "Rajasthani/Gujarati skirt-blouse set"),
    (9,  "Indo Western",  "Fusion of traditional and western styles"),
    (10, "Accessories",   "Jewellery, dupattas, turbans, and more"),
]

# (name, cat_id, size, color, fabric, occasion, price, deposit, qty_total, qty_avail, condition, description)
INVENTORY = [
    # ── Sarees (cat 1) ────────────────────────────────────────
    ("Banarasi Silk Saree – Gold Zari",      1, "Free Size", "Gold & Red",     "Banarasi Silk",   "Wedding",  900, 2500, 3, 3, "Excellent", "Heavy zari work Banarasi saree, perfect for bridal occasions"),
    ("Kanjivaram Silk Saree – Emerald",       1, "Free Size", "Emerald Green",  "Kanjivaram Silk", "Wedding", 1000, 3000, 2, 2, "Excellent", "Premium Kanjivaram with gold temple border"),
    ("Chikankari Saree – Ivory",              1, "Free Size", "Ivory White",    "Georgette",       "Festival",  500, 1000, 4, 4, "Good",      "Delicate hand-embroidered Lucknowi Chikankari"),
    ("Bandhani Saree – Mustard",              1, "Free Size", "Mustard Yellow", "Cotton Silk",     "Festival",  450,  900, 3, 3, "Good",      "Vibrant tie-dye Bandhani print from Gujarat"),
    ("Organza Saree – Pastel Pink",           1, "Free Size", "Pastel Pink",    "Organza",         "Party",     600, 1200, 2, 2, "Excellent", "Light floral organza saree with sequin border"),
    ("Paithani Saree – Purple Gold",          1, "Free Size", "Purple & Gold",  "Pure Silk",       "Wedding",  1100, 3000, 2, 2, "Excellent", "Authentic Paithani with peacock motif border"),
    ("Chanderi Saree – Sky Blue",             1, "Free Size", "Sky Blue",       "Chanderi Silk",   "Festival",  550, 1100, 3, 3, "Good",      "Lightweight Chanderi with silver zari stripes"),
    # ── Lehengas (cat 2) ─────────────────────────────────────
    ("Bridal Lehenga – Crimson Velvet",       2, "M",         "Crimson Red",    "Silk Velvet",     "Wedding",  2500, 5000, 2, 2, "Excellent", "Heavy embroidered bridal lehenga with dupatta"),
    ("Floral Net Lehenga – Pink",             2, "S",         "Pastel Pink",    "Net",             "Party",     900, 2000, 3, 3, "Good",      "Light floral net lehenga, ideal for sangeet"),
    ("Bandhani Lehenga – Yellow",             2, "L",         "Yellow",         "Cotton Silk",     "Festival",  700, 1500, 2, 2, "Good",      "Vibrant Bandhani print lehenga from Rajasthan"),
    ("Mirror Work Lehenga – Teal",            2, "M",         "Teal & Gold",    "Raw Silk",        "Wedding",  1800, 4000, 2, 2, "Excellent", "Intricate mirror and thread embroidery work"),
    ("Indo Fusion Lehenga – Mauve",           2, "L",         "Mauve",          "Georgette",       "Party",     950, 2000, 3, 3, "Good",      "Modern cut lehenga with contemporary prints"),
    ("Sharara Set – Bottle Green",            2, "M",         "Bottle Green",   "Crepe Silk",      "Wedding",  1300, 2800, 2, 2, "Excellent", "Flared sharara with heavily embroidered kurti"),
    # ── Salwar Kameez (cat 3) ────────────────────────────────
    ("Anarkali Suit – Royal Blue",            3, "M",         "Royal Blue",     "Georgette",       "Party",     600, 1200, 4, 4, "Excellent", "Floor-length Anarkali with churidar"),
    ("Patiala Suit – Orange Phulkari",        3, "L",         "Orange",         "Cotton",          "Festival",  350,  700, 5, 5, "Good",      "Embroidered Phulkari Patiala suit"),
    ("Palazzo Suit – Lavender",               3, "S",         "Lavender",       "Crepe",           "Casual",    400,  800, 4, 4, "Good",      "Comfortable palazzo pants with straight kurta"),
    ("Kashmiri Suit – Off White",             3, "M",         "Off White",      "Pashmina Blend",  "Festival",  750, 1500, 2, 2, "Excellent", "Hand-embroidered Kashmiri aari work suit"),
    # ── Sherwanis (cat 4) ────────────────────────────────────
    ("Groom Sherwani – Ivory Gold",           4, "L",         "Ivory & Gold",   "Brocade",         "Wedding",  3000, 6000, 2, 2, "Excellent", "Premium groom sherwani with gold embroidery"),
    ("Jodhpuri Sherwani – Navy Blue",         4, "M",         "Navy Blue",      "Wool Blend",      "Wedding",  2000, 4000, 2, 2, "Excellent", "Classic Jodhpuri bandhgala sherwani"),
    ("Sherwani – Champagne Beige",            4, "XL",        "Champagne",      "Silk Blend",      "Wedding",  2200, 4500, 2, 2, "Excellent", "Light embroidered sherwani for wedding guests"),
    ("Sherwani – Bottle Green",               4, "L",         "Bottle Green",   "Brocade",         "Wedding",  2800, 5500, 1, 1, "Excellent", "Heavily embroidered sherwani with churidar"),
    # ── Kurta Pajama (cat 5) ─────────────────────────────────
    ("Kurta Pajama – Mint Green",             5, "XL",        "Mint Green",     "Cotton",          "Festival",  400,  800, 6, 6, "Good",      "Embroidered kurta with straight pajama"),
    ("Silk Kurta Pajama – Maroon",            5, "L",         "Maroon",         "Pure Silk",       "Wedding",   800, 1500, 3, 3, "Excellent", "Luxurious silk kurta for wedding receptions"),
    ("Nehru Jacket Set – Charcoal",           5, "M",         "Charcoal Grey",  "Linen",           "Party",     550, 1100, 4, 4, "Good",      "Nehru collar kurta with matching jacket"),
    ("Pathani Suit – Cream",                  5, "XL",        "Cream",          "Cotton Linen",    "Casual",    350,  700, 5, 5, "Good",      "Comfortable Pathani kurta pajama set"),
    # ── Anarkali (cat 6) ─────────────────────────────────────
    ("Anarkali Gown – Wine Red",              6, "M",         "Wine Red",       "Velvet",          "Wedding",  1200, 2500, 2, 2, "Excellent", "Full-length velvet Anarkali with sequin work"),
    ("Anarkali Suit – Turquoise",             6, "S",         "Turquoise",      "Georgette",       "Party",     700, 1400, 3, 3, "Good",      "Printed Anarkali with contrast dupatta"),
    # ── Dhoti Kurta (cat 7) ──────────────────────────────────
    ("Dhoti Kurta – White Gold",              7, "Free Size", "White & Gold",   "Cotton Silk",     "Wedding",   600, 1200, 4, 4, "Good",      "Traditional South Indian dhoti with kurta"),
    ("Dhoti Kurta – Saffron",                 7, "Free Size", "Saffron",        "Pure Cotton",     "Festival",  450,  900, 3, 3, "Good",      "Vibrant saffron dhoti kurta for festivals"),
    # ── Ghagra Choli (cat 8) ─────────────────────────────────
    ("Ghagra Choli – Mirror Work",            8, "M",         "Multicolor",     "Cotton Silk",     "Festival",  750, 1500, 3, 3, "Good",      "Traditional mirror-work Rajasthani ghagra choli"),
    ("Chaniya Choli – Navratri Special",      8, "S",         "Bright Orange",  "Cotton",          "Festival",  500, 1000, 4, 4, "Good",      "Colorful chaniya choli for Navratri celebrations"),
    # ── Indo Western (cat 9) ─────────────────────────────────
    ("Indo Western Sherwani – Grey",          9, "M",         "Charcoal Grey",  "Polyester Blend", "Party",    1200, 2500, 2, 2, "Excellent", "Modern Indo-western sherwani with slim fit"),
    ("Fusion Kurta – Black Gold",             9, "L",         "Black & Gold",   "Silk Blend",      "Party",     900, 1800, 3, 3, "Good",      "Contemporary fusion kurta with gold print"),
    # ── Accessories (cat 10) ─────────────────────────────────
    ("Bridal Jewellery Set – Kundan",        10, "Free Size", "Gold & Red",     "Metal/Stone",     "Wedding",   800, 2000, 3, 3, "Excellent", "Full kundan bridal set: necklace, earrings, maang tikka"),
    ("Turban – Royal Blue",                  10, "Free Size", "Royal Blue",     "Silk",            "Wedding",   200,  400, 5, 5, "Good",      "Silk pagdi/turban for groom and groomsmen"),
]

CUSTOMERS = [
    ("Priya Sharma",     "9876543210", "priya.sharma@email.com",    "12, Rose Lane, Andheri West, Mumbai 400053",          "Aadhar",          "2345 6789 0123"),
    ("Rohan Mehta",      "9823456780", "rohan.mehta@email.com",     "45, Shivaji Nagar, Pune 411005",                      "PAN",             "ABCDE1234F"),
    ("Ananya Verma",     "9712345678", "ananya.v@email.com",        "7, Green Park Extension, New Delhi 110016",           "Aadhar",          "9876 5432 1098"),
    ("Vikram Singh",     "9654321098", "vikram.s@email.com",        "22, MG Road, Indiranagar, Bangalore 560038",          "Passport",        "P1234567"),
    ("Deepika Patel",    "9543210987", "deepika.p@email.com",       "89, Navrangpura, Ahmedabad 380009",                   "Voter ID",        "GJ/24/123/456789"),
    ("Arjun Nair",       "9432109876", "arjun.nair@email.com",      "34, Kakkanad, Kochi, Kerala 682030",                  "Driving Licence", "KL0120230012345"),
    ("Meera Joshi",      "9321098765", "meera.j@email.com",         "56, FC Road, Camp, Pune 411001",                      "Aadhar",          "1122 3344 5566"),
    ("Karan Kapoor",     "9210987654", "karan.k@email.com",         "88, Sector 18, Noida 201301",                         "PAN",             "FGHIJ5678K"),
    ("Sneha Iyer",       "9109876543", "sneha.iyer@email.com",      "23, T Nagar, Chennai 600017",                         "Aadhar",          "7788 9900 1122"),
    ("Rahul Gupta",      "9098765432", "rahul.g@email.com",         "67, Hazratganj, Lucknow 226001",                      "Voter ID",        "UP/12/789/012345"),
    ("Pooja Desai",      "8987654321", "pooja.d@email.com",         "14, Banjara Hills, Hyderabad 500034",                 "PAN",             "LMNOP9012Q"),
    ("Amit Choudhary",   "8876543210", "amit.c@email.com",          "3, Vaishali Nagar, Jaipur 302021",                    "Aadhar",          "3344 5566 7788"),
    ("Sunita Rao",       "8765432109", "sunita.r@email.com",        "78, Koramangala, Bangalore 560034",                   "Passport",        "P9876543"),
    ("Nikhil Sharma",    "8654321098", "nikhil.s@email.com",        "5, Salt Lake, Kolkata 700064",                        "Aadhar",          "5566 7788 9900"),
    ("Kavya Menon",      "8543210987", "kavya.m@email.com",         "19, Palarivattom, Kochi 682025",                      "Driving Licence", "KL0420240056789"),
]

# ──────────────────────────────────────────────────────────────
#  RENTALS
#  Each entry: (cust_idx, rent_offset, due_offset, status, items, notes)
#  items: list of (inv_idx, qty)
#  For "Partial": first item returned, second still out
# ──────────────────────────────────────────────────────────────
RENTALS = [
    # ── Returned (10) ────────────────────────────────────────
    (0,  -35, -28, "Returned", [(0,1),(2,1)],  "Bridal event – Mumbai"),
    (1,  -32, -25, "Returned", [(17,1)],        "Groom outfit – cousin's wedding"),
    (2,  -28, -21, "Returned", [(7,1),(8,1)],   "Sangeet function"),
    (3,  -25, -18, "Returned", [(16,1)],         "Wedding reception – Bangalore"),
    (4,  -22, -15, "Returned", [(28,1),(29,1)],  "Navratri celebrations"),
    (5,  -18, -12, "Returned", [(20,1),(21,1)],  "Festival occasion"),
    (6,  -15, -10, "Returned", [(1,1),(4,1)],    "Diwali party"),
    (7,  -12,  -6, "Returned", [(12,1),(23,1)],  "Corporate ethnic day"),
    (8,   -9,  -3, "Returned", [(3,1)],           "Friend's wedding"),
    (9,   -7,  -2, "Returned", [(18,1)],           "Anniversary dinner"),
    # ── Active – due in future (7) ───────────────────────────
    (0,   -4,   3, "Active",   [(0,1),(5,1)],   "Wedding event this week"),
    (2,   -3,   4, "Active",   [(16,1)],          "Groom rental – Saturday wedding"),
    (4,   -2,   5, "Active",   [(9,1),(10,1)],  "Engagement ceremony"),
    (6,   -3,   6, "Active",   [(22,1),(25,1)], "Reception and sangeet"),
    (10,  -1,   7, "Active",   [(1,1)],           "Festival function"),
    (11,  -2,   4, "Active",   [(33,1),(34,1)], "Bridal jewellery + groom turban"),
    (12,  -1,   5, "Active",   [(6,1)],           "Paithani for mehendi ceremony"),
    # ── Overdue – due date already passed (3) ────────────────
    (7,  -14,  -4, "Overdue",  [(2,1),(13,1)],  ""),
    (8,  -10,  -2, "Overdue",  [(19,1)],          ""),
    (13, -12,  -3, "Overdue",  [(7,1)],            "Delayed return – customer travelling"),
    # ── Cancelled (3) ────────────────────────────────────────
    (9,   -6,   1, "Cancelled", [(7,1)],           "Event cancelled due to illness"),
    (10,  -4,   3, "Cancelled", [(13,1)],           "Duplicate booking – refunded"),
    (14,  -2,   5, "Cancelled", [(8,1)],            "Customer changed mind"),
    # ── Partial returns (2) – rental stays Active ────────────
    # Customer took 2 items; has returned 1 (returned_at set), 1 still out
    (3,   -8,   2, "Active",   [(0,1),(26,1)],  "Partial return – saree returned, ghagra still out"),
    (5,   -5,   3, "Active",   [(21,1),(27,1)], "Partial return – kurta returned, chaniya still out"),
]


# ──────────────────────────────────────────────────────────────
def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cur  = conn.cursor()

    # ── Wipe existing data ────────────────────────────────────
    print("Clearing existing data…")
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    for t in ["rental_items", "rentals", "inventory", "customers", "categories"]:
        cur.execute(f"TRUNCATE TABLE {t}")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()

    # ── Categories ───────────────────────────────────────────
    print("Inserting categories…")
    for row in CATEGORIES:
        cur.execute("INSERT INTO categories (id, name, description) VALUES (%s,%s,%s)", row)
    conn.commit()

    # ── Inventory ────────────────────────────────────────────
    print("Inserting inventory…")
    for row in INVENTORY:
        cur.execute(
            "INSERT INTO inventory (name, category_id, size, color, fabric, occasion, "
            "rental_price, deposit_amount, quantity_total, quantity_available, "
            "condition_status, description) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            row
        )
    conn.commit()

    # ── Customers ────────────────────────────────────────────
    print("Inserting customers…")
    for row in CUSTOMERS:
        cur.execute(
            "INSERT INTO customers (name, phone, email, address, id_proof_type, id_proof_number) "
            "VALUES (%s,%s,%s,%s,%s,%s)", row
        )
    conn.commit()

    # Fetch assigned IDs
    cur.execute("SELECT id FROM customers ORDER BY id")
    cust_ids = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT id, rental_price, deposit_amount FROM inventory ORDER BY id")
    inv_map = {i: (iid, float(p), float(d)) for i, (iid, p, d) in enumerate(cur.fetchall())}

    # ── Rentals ──────────────────────────────────────────────
    print("Inserting rentals…")
    today = date.today()
    total_rentals = len(RENTALS)

    for idx, (cust_idx, rent_off, due_off, status, item_specs, notes) in enumerate(RENTALS):
        rental_date = today + timedelta(days=rent_off)
        due_date    = today + timedelta(days=due_off)
        cust_id     = cust_ids[cust_idx]
        code        = f"EWR-{rental_date.strftime('%Y%m%d')}-{idx+1:04d}"

        # Resolve items
        line_items = []
        total_amt  = 0.0
        deposit    = 0.0
        for inv_idx, qty in item_specs:
            if inv_idx not in inv_map:
                continue
            iid, price, dep = inv_map[inv_idx]
            total_amt += price * qty
            deposit   += dep   * qty
            line_items.append((iid, qty, price))

        # Rental-level fields
        actual_return = None
        late_fee      = 0.0
        is_partial    = notes.startswith("Partial return")

        if status == "Returned":
            actual_return = due_date
        elif status == "Overdue":
            days_late = abs(due_off)
            late_fee  = 50.0 * days_late

        cur.execute(
            "INSERT INTO rentals (rental_code, customer_id, rental_date, return_due_date, "
            "actual_return_date, total_amount, deposit_paid, late_fee, status, notes) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (code, cust_id, rental_date, due_date, actual_return,
             total_amt, deposit, late_fee, status, notes)
        )
        conn.commit()
        rental_id = cur.lastrowid

        for item_seq, (iid, qty, unit_price) in enumerate(line_items):
            # For Returned rentals → mark returned_at on all items
            if status == "Returned":
                returned_at = due_date
            # For Partial rentals → first item returned, rest still out
            elif is_partial and item_seq == 0:
                returned_at = today + timedelta(days=rent_off + 3)
            else:
                returned_at = None

            cur.execute(
                "INSERT INTO rental_items (rental_id, inventory_id, quantity, unit_price, returned_at) "
                "VALUES (%s,%s,%s,%s,%s)",
                (rental_id, iid, qty, unit_price, returned_at)
            )

            # Reduce available stock for items still out (Active / Overdue / unreturned partial)
            if status in ("Active", "Overdue") or (is_partial and returned_at is None):
                cur.execute(
                    "UPDATE inventory SET quantity_available = GREATEST(0, quantity_available - %s) "
                    "WHERE id = %s", (qty, iid)
                )

        conn.commit()

    cur.close()
    conn.close()

    returned  = sum(1 for r in RENTALS if r[3] == "Returned")
    active    = sum(1 for r in RENTALS if r[3] == "Active" and not r[5].startswith("Partial"))
    overdue   = sum(1 for r in RENTALS if r[3] == "Overdue")
    cancelled = sum(1 for r in RENTALS if r[3] == "Cancelled")
    partial   = sum(1 for r in RENTALS if r[5].startswith("Partial"))

    print()
    print("=" * 52)
    print("   Padmavati Novelty Stores — Data Loaded!")
    print("=" * 52)
    print(f"   Categories  : {len(CATEGORIES)}")
    print(f"   Inventory   : {len(INVENTORY)} items across 10 categories")
    print(f"   Customers   : {len(CUSTOMERS)}")
    print(f"   Rentals     : {total_rentals} total")
    print(f"     Returned  : {returned}")
    print(f"     Active    : {active}")
    print(f"     Overdue   : {overdue}")
    print(f"     Cancelled : {cancelled}")
    print(f"     Partial   : {partial}  (1 item returned, 1 still out)")
    print()
    print("   Run again anytime to reset to this state.")
    print("=" * 52)


if __name__ == "__main__":
    main()
