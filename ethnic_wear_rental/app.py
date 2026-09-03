import os
import json
from datetime import date, datetime
from decimal import Decimal
from flask import Flask, render_template, request, Response, redirect, url_for
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "ethnic_wear_secret_2024")

# ─── DB Config ────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "ethnic_wear_rental"),
    "charset":  "utf8mb4",
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def query(sql, params=None, fetch="all", commit=False):
    conn = get_db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    if commit:
        conn.commit()
        last_id = cur.lastrowid
        cur.close(); conn.close()
        return last_id
    result = cur.fetchall() if fetch == "all" else cur.fetchone()
    cur.close(); conn.close()
    return result

# ─── Serialiser: handles Decimal, date, datetime ─────────────────────────────
def _serial(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def _jsonify(payload, status=200):
    return Response(
        json.dumps(payload, default=_serial),
        status=status,
        mimetype="application/json"
    )

def success(data=None, message="Success"):
    return _jsonify({"status": "success", "message": message, "data": data})

def error(message="Error", code=400):
    return _jsonify({"status": "error", "message": message}, status=code)

def generate_rental_code():
    row = query("SELECT COUNT(*) as cnt FROM rentals", fetch="one")
    cnt = int(row["cnt"]) if row else 0
    return f"EWR-{date.today().strftime('%Y%m%d')}-{cnt + 1:04d}"

# ─── Pages ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/inventory")
def inventory_page():
    return render_template("inventory.html")

@app.route("/customers")
def customers_page():
    return render_template("customers.html")

@app.route("/rentals")
def rentals_page():
    return render_template("rentals.html")

# ═══════════════════════════════════════════════════════════════════════════════
#  API – DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/dashboard/stats")
def api_dashboard_stats():
    total_items     = int(query("SELECT COALESCE(SUM(quantity_total),0) as v FROM inventory",     fetch="one")["v"])
    available_items = int(query("SELECT COALESCE(SUM(quantity_available),0) as v FROM inventory", fetch="one")["v"])
    total_customers = int(query("SELECT COUNT(*) as v FROM customers",          fetch="one")["v"])
    active_rentals  = int(query("SELECT COUNT(*) as v FROM rentals WHERE status='Active'",  fetch="one")["v"])
    overdue_rentals = int(query("SELECT COUNT(*) as v FROM rentals WHERE status='Overdue'", fetch="one")["v"])
    monthly_revenue = float(query("""
        SELECT COALESCE(SUM(total_amount + deposit_paid), 0) as v FROM rentals
        WHERE status IN ('Active','Returned')
          AND MONTH(rental_date)=MONTH(CURDATE())
          AND YEAR(rental_date)=YEAR(CURDATE())
    """, fetch="one")["v"])
    total_revenue = float(query("""
        SELECT COALESCE(SUM(total_amount + deposit_paid), 0) as v FROM rentals
        WHERE status IN ('Active','Returned')
    """, fetch="one")["v"])
    return success({
        "total_items":     total_items,
        "available_items": available_items,
        "rented_items":    total_items - available_items,
        "total_customers": total_customers,
        "active_rentals":  active_rentals,
        "overdue_rentals": overdue_rentals,
        "monthly_revenue": monthly_revenue,
        "total_revenue":   total_revenue,
    })

@app.route("/api/dashboard/recent_rentals")
def api_recent_rentals():
    rows = query("""
        SELECT r.id, r.rental_code, c.name AS customer_name,
               r.rental_date, r.return_due_date, r.status, r.total_amount
        FROM rentals r JOIN customers c ON c.id = r.customer_id
        ORDER BY r.created_at DESC LIMIT 8
    """)
    return success(rows)

@app.route("/api/dashboard/category_stats")
def api_category_stats():
    rows = query("""
        SELECT c.name,
               COUNT(i.id) as item_count,
               COALESCE(SUM(i.quantity_total - i.quantity_available), 0) as rented_count
        FROM categories c
        LEFT JOIN inventory i ON i.category_id = c.id
        GROUP BY c.id, c.name
        ORDER BY item_count DESC
    """)
    return success(rows)

@app.route("/api/dashboard/overdue")
def api_dashboard_overdue():
    rows = query("""
        SELECT r.id, r.rental_code, c.name AS customer_name, c.phone,
               r.return_due_date,
               DATEDIFF(CURDATE(), r.return_due_date) AS days_overdue,
               r.total_amount
        FROM rentals r JOIN customers c ON c.id = r.customer_id
        WHERE r.status = 'Overdue'
        ORDER BY r.return_due_date ASC
    """)
    return success(rows)

# ═══════════════════════════════════════════════════════════════════════════════
#  API – CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/categories")
def api_get_categories():
    return success(query("SELECT * FROM categories ORDER BY name"))

# ═══════════════════════════════════════════════════════════════════════════════
#  API – INVENTORY
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/inventory", methods=["GET"])
def api_get_inventory():
    search   = request.args.get("search", "")
    category = request.args.get("category", "")
    size     = request.args.get("size", "")
    status   = request.args.get("status", "")
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 12))
    offset   = (page - 1) * per_page

    where, params = [], []
    if search:
        where.append("(i.name LIKE %s OR i.color LIKE %s OR i.fabric LIKE %s OR i.occasion LIKE %s)")
        like = f"%{search}%"
        params.extend([like, like, like, like])
    if category:
        where.append("i.category_id = %s")
        params.append(int(category))
    if size:
        where.append("i.size = %s")
        params.append(size)
    if status == "available":
        where.append("i.quantity_available > 0")
    elif status == "rented":
        where.append("i.quantity_available = 0")

    wc = ("WHERE " + " AND ".join(where)) if where else ""

    items = query(
        f"SELECT i.*, c.name AS category_name FROM inventory i "
        f"JOIN categories c ON c.id = i.category_id {wc} "
        f"ORDER BY i.updated_at DESC LIMIT %s OFFSET %s",
        params + [per_page, offset]
    )
    total = int(query(
        f"SELECT COUNT(*) as v FROM inventory i "
        f"JOIN categories c ON c.id = i.category_id {wc}",
        params, fetch="one"
    )["v"])

    return success({
        "items":    items,
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "pages":    max(1, (total + per_page - 1) // per_page),
    })

@app.route("/api/inventory/<int:item_id>", methods=["GET"])
def api_get_inventory_item(item_id):
    item = query(
        "SELECT i.*, c.name AS category_name FROM inventory i "
        "JOIN categories c ON c.id = i.category_id WHERE i.id = %s",
        (item_id,), fetch="one"
    )
    if not item:
        return error("Item not found", 404)
    return success(item)

@app.route("/api/inventory", methods=["POST"])
def api_add_inventory():
    d = request.get_json()
    for f in ["name", "category_id", "size", "color", "rental_price", "quantity_total"]:
        if not d.get(f):
            return error(f"Field '{f}' is required")
    qty = int(d["quantity_total"])
    new_id = query(
        "INSERT INTO inventory (name, category_id, size, color, fabric, occasion, "
        "rental_price, deposit_amount, quantity_total, quantity_available, "
        "condition_status, description, image_url) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (d["name"], int(d["category_id"]), d["size"], d["color"],
         d.get("fabric", ""), d.get("occasion", ""),
         float(d["rental_price"]), float(d.get("deposit_amount", 0)),
         qty, qty, d.get("condition_status", "Excellent"),
         d.get("description", ""), d.get("image_url", "")),
        commit=True
    )
    return success({"id": new_id}, "Item added successfully")

@app.route("/api/inventory/<int:item_id>", methods=["PUT"])
def api_update_inventory(item_id):
    d    = request.get_json()
    item = query("SELECT * FROM inventory WHERE id=%s", (item_id,), fetch="one")
    if not item:
        return error("Item not found", 404)
    qty_total = int(d.get("quantity_total", item["quantity_total"]))
    rented    = int(item["quantity_total"]) - int(item["quantity_available"])
    qty_avail = max(0, qty_total - rented)
    query(
        "UPDATE inventory SET name=%s, category_id=%s, size=%s, color=%s, fabric=%s, "
        "occasion=%s, rental_price=%s, deposit_amount=%s, quantity_total=%s, "
        "quantity_available=%s, condition_status=%s, description=%s, image_url=%s "
        "WHERE id=%s",
        (d.get("name",             item["name"]),
         int(d.get("category_id",  item["category_id"])),
         d.get("size",             item["size"]),
         d.get("color",            item["color"]),
         d.get("fabric",           item.get("fabric") or ""),
         d.get("occasion",         item.get("occasion") or ""),
         float(d.get("rental_price",  item["rental_price"])),
         float(d.get("deposit_amount",item["deposit_amount"])),
         qty_total, qty_avail,
         d.get("condition_status", item["condition_status"]),
         d.get("description",      item.get("description") or ""),
         d.get("image_url",        item.get("image_url") or ""),
         item_id),
        commit=True
    )
    return success(message="Item updated successfully")

@app.route("/api/inventory/<int:item_id>", methods=["DELETE"])
def api_delete_inventory(item_id):
    cnt = int(query(
        "SELECT COUNT(*) as v FROM rental_items ri "
        "JOIN rentals r ON r.id = ri.rental_id "
        "WHERE ri.inventory_id=%s AND r.status IN ('Active','Overdue')",
        (item_id,), fetch="one"
    )["v"])
    if cnt > 0:
        return error("Cannot delete: item is currently rented out")
    query("DELETE FROM inventory WHERE id=%s", (item_id,), commit=True)
    return success(message="Item deleted successfully")

# ═══════════════════════════════════════════════════════════════════════════════
#  API – CUSTOMERS
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/customers", methods=["GET"])
def api_get_customers():
    search   = request.args.get("search", "")
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 12))
    offset   = (page - 1) * per_page

    where, params = [], []
    if search:
        where.append("(c.name LIKE %s OR c.phone LIKE %s OR c.email LIKE %s)")
        like = f"%{search}%"
        params.extend([like, like, like])

    wc = ("WHERE " + " AND ".join(where)) if where else ""
    rows = query(
        f"SELECT c.*, COUNT(r.id) AS total_rentals, "
        f"SUM(CASE WHEN r.status='Active' THEN 1 ELSE 0 END) AS active_rentals "
        f"FROM customers c LEFT JOIN rentals r ON r.customer_id = c.id "
        f"{wc} GROUP BY c.id ORDER BY c.created_at DESC LIMIT %s OFFSET %s",
        params + [per_page, offset]
    )
    total = int(query(
        f"SELECT COUNT(*) as v FROM customers c {wc}",
        params, fetch="one"
    )["v"])
    return success({
        "customers": rows,
        "total":     total,
        "page":      page,
        "per_page":  per_page,
        "pages":     max(1, (total + per_page - 1) // per_page),
    })

@app.route("/api/customers/<int:customer_id>", methods=["GET"])
def api_get_customer(customer_id):
    cust = query("SELECT * FROM customers WHERE id=%s", (customer_id,), fetch="one")
    if not cust:
        return error("Customer not found", 404)
    rentals = query(
        "SELECT r.*, COUNT(ri.id) as item_count FROM rentals r "
        "LEFT JOIN rental_items ri ON ri.rental_id = r.id "
        "WHERE r.customer_id=%s GROUP BY r.id ORDER BY r.rental_date DESC",
        (customer_id,)
    )
    return success({"customer": cust, "rentals": rentals})

@app.route("/api/customers", methods=["POST"])
def api_add_customer():
    d = request.get_json()
    if not d.get("name") or not d.get("phone"):
        return error("Name and phone are required")
    if query("SELECT id FROM customers WHERE phone=%s", (d["phone"],), fetch="one"):
        return error("A customer with this phone number already exists")
    new_id = query(
        "INSERT INTO customers (name, phone, email, address, id_proof_type, id_proof_number) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (d["name"], d["phone"], d.get("email",""), d.get("address",""),
         d.get("id_proof_type","Aadhar"), d.get("id_proof_number","")),
        commit=True
    )
    return success({"id": new_id}, "Customer added successfully")

@app.route("/api/customers/<int:customer_id>", methods=["PUT"])
def api_update_customer(customer_id):
    d    = request.get_json()
    cust = query("SELECT * FROM customers WHERE id=%s", (customer_id,), fetch="one")
    if not cust:
        return error("Customer not found", 404)
    query(
        "UPDATE customers SET name=%s, phone=%s, email=%s, address=%s, "
        "id_proof_type=%s, id_proof_number=%s WHERE id=%s",
        (d.get("name",            cust["name"]),
         d.get("phone",           cust["phone"]),
         d.get("email",           cust.get("email") or ""),
         d.get("address",         cust.get("address") or ""),
         d.get("id_proof_type",   cust["id_proof_type"]),
         d.get("id_proof_number", cust.get("id_proof_number") or ""),
         customer_id),
        commit=True
    )
    return success(message="Customer updated successfully")

@app.route("/api/customers/<int:customer_id>", methods=["DELETE"])
def api_delete_customer(customer_id):
    cnt = int(query(
        "SELECT COUNT(*) as v FROM rentals "
        "WHERE customer_id=%s AND status IN ('Active','Overdue')",
        (customer_id,), fetch="one"
    )["v"])
    if cnt > 0:
        return error("Cannot delete: customer has active rentals")
    query("DELETE FROM customers WHERE id=%s", (customer_id,), commit=True)
    return success(message="Customer deleted successfully")

# ═══════════════════════════════════════════════════════════════════════════════
#  API – RENTALS
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/rentals", methods=["GET"])
def api_get_rentals():
    search   = request.args.get("search", "")
    # support multiple status= params e.g. ?status=Active&status=Overdue
    statuses = request.args.getlist("status")
    statuses = [s for s in statuses if s]   # drop empty strings
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    offset   = (page - 1) * per_page

    # Auto-mark overdue
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE rentals SET status='Overdue' WHERE status='Active' AND return_due_date < CURDATE()")
    conn.commit(); cur.close(); conn.close()

    where, params = [], []
    if search:
        where.append("(r.rental_code LIKE %s OR c.name LIKE %s OR c.phone LIKE %s)")
        like = f"%{search}%"
        params.extend([like, like, like])
    if statuses:
        placeholders = ",".join(["%s"] * len(statuses))
        where.append(f"r.status IN ({placeholders})")
        params.extend(statuses)

    wc = ("WHERE " + " AND ".join(where)) if where else ""
    rows = query(
        f"SELECT r.*, c.name AS customer_name, c.phone AS customer_phone, "
        f"COUNT(ri.id) AS item_count, "
        f"SUM(CASE WHEN ri.returned_at IS NOT NULL THEN 1 ELSE 0 END) AS returned_count "
        f"FROM rentals r JOIN customers c ON c.id = r.customer_id "
        f"LEFT JOIN rental_items ri ON ri.rental_id = r.id "
        f"{wc} GROUP BY r.id ORDER BY r.created_at DESC LIMIT %s OFFSET %s",
        params + [per_page, offset]
    )
    total = int(query(
        f"SELECT COUNT(*) as v FROM rentals r "
        f"JOIN customers c ON c.id = r.customer_id {wc}",
        params, fetch="one"
    )["v"])
    return success({
        "rentals":  rows,
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "pages":    max(1, (total + per_page - 1) // per_page),
    })

@app.route("/api/rentals/<int:rental_id>", methods=["GET"])
def api_get_rental(rental_id):
    rental = query(
        "SELECT r.*, c.name AS customer_name, c.phone AS customer_phone, "
        "c.email AS customer_email "
        "FROM rentals r JOIN customers c ON c.id = r.customer_id WHERE r.id=%s",
        (rental_id,), fetch="one"
    )
    if not rental:
        return error("Rental not found", 404)
    items = query(
        "SELECT ri.*, i.name AS item_name, i.size, i.color, cat.name AS category_name "
        "FROM rental_items ri JOIN inventory i ON i.id = ri.inventory_id "
        "JOIN categories cat ON cat.id = i.category_id WHERE ri.rental_id=%s "
        "ORDER BY ri.returned_at IS NULL DESC, ri.id ASC",
        (rental_id,)
    )
    return success({"rental": rental, "items": items})

@app.route("/api/rentals", methods=["POST"])
def api_create_rental():
    d = request.get_json()
    for f in ["customer_id", "rental_date", "return_due_date", "items"]:
        if not d.get(f):
            return error(f"Field '{f}' is required")
    if not d["items"]:
        return error("At least one item is required")

    if not query("SELECT id FROM customers WHERE id=%s", (d["customer_id"],), fetch="one"):
        return error("Customer not found")

    total_amount = 0.0; deposit_total = 0.0; validated = []
    for it in d["items"]:
        inv = query("SELECT * FROM inventory WHERE id=%s", (it["inventory_id"],), fetch="one")
        if not inv:
            return error(f"Item {it['inventory_id']} not found")
        qty = int(it.get("quantity", 1))
        if int(inv["quantity_available"]) < qty:
            return error(f"Not enough stock for '{inv['name']}'")
        total_amount  += float(inv["rental_price"])  * qty
        deposit_total += float(inv["deposit_amount"]) * qty
        validated.append({"inventory_id": int(it["inventory_id"]),
                          "quantity": qty, "unit_price": float(inv["rental_price"])})

    rental_code = generate_rental_code()
    conn = get_db(); cur = conn.cursor()
    cur.execute(
        "INSERT INTO rentals (rental_code, customer_id, rental_date, return_due_date, "
        "total_amount, deposit_paid, status, notes) VALUES (%s,%s,%s,%s,%s,%s,'Active',%s)",
        (rental_code, int(d["customer_id"]), d["rental_date"], d["return_due_date"],
         total_amount, deposit_total, d.get("notes", ""))
    )
    conn.commit()
    rental_id = cur.lastrowid
    for it in validated:
        cur.execute(
            "INSERT INTO rental_items (rental_id, inventory_id, quantity, unit_price) "
            "VALUES (%s,%s,%s,%s)",
            (rental_id, it["inventory_id"], it["quantity"], it["unit_price"])
        )
        cur.execute(
            "UPDATE inventory SET quantity_available = quantity_available - %s WHERE id=%s",
            (it["quantity"], it["inventory_id"])
        )
    conn.commit(); cur.close(); conn.close()
    return success({"id": rental_id, "rental_code": rental_code}, "Rental created successfully")

@app.route("/api/rentals/<int:rental_id>/items", methods=["GET"])
def api_get_rental_items(rental_id):
    """Return all line-items for a rental with their return status."""
    rental = query("SELECT * FROM rentals WHERE id=%s", (rental_id,), fetch="one")
    if not rental:
        return error("Rental not found", 404)
    items = query(
        "SELECT ri.*, i.name AS item_name, i.size, i.color, "
        "cat.name AS category_name "
        "FROM rental_items ri "
        "JOIN inventory i   ON i.id  = ri.inventory_id "
        "JOIN categories cat ON cat.id = i.category_id "
        "WHERE ri.rental_id = %s",
        (rental_id,)
    )
    return success(items)


@app.route("/api/rentals/<int:rental_id>/return", methods=["POST"])
def api_return_rental(rental_id):
    """
    Partial or full return.

    Body (JSON):
      return_date       : "YYYY-MM-DD"  (default: today)
      late_fee_per_day  : number        (default: 50)
      item_ids          : [int, ...]    IDs from rental_items to return NOW.
                          Omit / pass null to return ALL unreturned items.
      return_note       : string        Optional note per batch
    """
    d      = request.get_json() or {}
    rental = query("SELECT * FROM rentals WHERE id=%s", (rental_id,), fetch="one")
    if not rental:
        return error("Rental not found", 404)
    if rental["status"] == "Cancelled":
        return error("Cancelled rental cannot be returned")
    if rental["status"] == "Returned":
        return error("All items already returned")

    return_date = d.get("return_date", date.today().isoformat())
    ret_dt = datetime.strptime(return_date, "%Y-%m-%d").date()
    due_dt = rental["return_due_date"]
    if isinstance(due_dt, str):
        due_dt = datetime.strptime(due_dt, "%Y-%m-%d").date()

    late_fee_per_day = float(d.get("late_fee_per_day", 50))
    return_note      = d.get("return_note", "")

    # All line-items for this rental
    all_items = query(
        "SELECT * FROM rental_items WHERE rental_id=%s", (rental_id,)
    )

    # Which item IDs to return in this batch
    requested_ids = d.get("item_ids")   # None means "return all unreturned"

    to_return = []
    for it in all_items:
        already_returned = it["returned_at"] is not None
        if already_returned:
            continue
        if requested_ids is None or it["id"] in requested_ids:
            to_return.append(it)

    if not to_return:
        return error("No unreturned items matched your selection")

    conn = get_db(); cur = conn.cursor()

    # Mark selected items as returned & restore stock
    for it in to_return:
        cur.execute(
            "UPDATE rental_items "
            "SET returned_at=%s, return_note=%s "
            "WHERE id=%s",
            (return_date, return_note, it["id"])
        )
        cur.execute(
            "UPDATE inventory "
            "SET quantity_available = quantity_available + %s "
            "WHERE id=%s",
            (it["quantity"], it["inventory_id"])
        )

    conn.commit()

    # Check if ALL items are now returned
    remaining = query(
        "SELECT COUNT(*) as v FROM rental_items "
        "WHERE rental_id=%s AND returned_at IS NULL",
        (rental_id,), fetch="one"
    )["v"]

    # Calculate late fee only on items returned late
    late_fee = 0.0
    if ret_dt > due_dt:
        late_fee = late_fee_per_day * (ret_dt - due_dt).days

    if int(remaining) == 0:
        # All items returned → close the rental
        existing_late = float(rental.get("late_fee") or 0)
        total_late    = existing_late + late_fee
        cur.execute(
            "UPDATE rentals "
            "SET status='Returned', actual_return_date=%s, late_fee=%s "
            "WHERE id=%s",
            (return_date, total_late, rental_id)
        )
        conn.commit()
        msg = "All items returned — rental closed"
        fully_returned = True
    else:
        # Partial return — accumulate late fee, keep rental Active/Overdue
        existing_late = float(rental.get("late_fee") or 0)
        cur.execute(
            "UPDATE rentals SET late_fee=%s WHERE id=%s",
            (existing_late + late_fee, rental_id)
        )
        conn.commit()
        msg = f"{len(to_return)} item(s) returned — {int(remaining)} still out"
        fully_returned = False

    cur.close(); conn.close()

    return success({
        "late_fee":       late_fee,
        "items_returned": len(to_return),
        "items_remaining": int(remaining),
        "fully_returned": fully_returned,
    }, msg)

@app.route("/api/rentals/<int:rental_id>/cancel", methods=["POST"])
def api_cancel_rental(rental_id):
    rental = query("SELECT * FROM rentals WHERE id=%s", (rental_id,), fetch="one")
    if not rental:
        return error("Rental not found", 404)
    if rental["status"] not in ("Active", "Overdue"):
        return error(f"Cannot cancel a '{rental['status']}' rental")

    items = query("SELECT * FROM rental_items WHERE rental_id=%s", (rental_id,))
    conn = get_db(); cur = conn.cursor()
    for it in items:
        cur.execute(
            "UPDATE inventory SET quantity_available = quantity_available + %s WHERE id=%s",
            (it["quantity"], it["inventory_id"])
        )
    cur.execute("UPDATE rentals SET status='Cancelled' WHERE id=%s", (rental_id,))
    conn.commit(); cur.close(); conn.close()
    return success(message="Rental cancelled successfully")

# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
