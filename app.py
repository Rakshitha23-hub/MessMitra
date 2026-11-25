
import math
import sqlite3
import os
from datetime import date, datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    flash,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database.db import get_db, initialize_database


# ---------------- APP CONFIGURATION ----------------

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "messmitra_local_development_key_change_before_deployment"
)


# ---------------- LOGIN PROTECTION ----------------

@app.before_request
def require_login():

    allowed_routes = ["login", "register", "static"]

    if request.endpoint is None:
        return

    if request.endpoint not in allowed_routes:
        if "user_id" not in session:
            return redirect(url_for("login"))


# ---------------- HOME / DASHBOARD ----------------

@app.route("/")
def dashboard():

    conn = get_db()

    meals = conn.execute(
        "SELECT * FROM meals ORDER BY id DESC"
    ).fetchall()

    inventory = conn.execute(
        "SELECT * FROM inventory ORDER BY expiry ASC"
    ).fetchall()

    surplus = conn.execute(
        "SELECT * FROM surplus ORDER BY id DESC"
    ).fetchall()

    stats = conn.execute("""
        SELECT
            COALESCE(SUM(prepared), 0) AS prepared,
            COALESCE(SUM(consumed), 0) AS consumed,
            COALESCE(SUM(wasted), 0) AS wasted
        FROM meals
    """).fetchone()

    prepared = stats["prepared"]
    consumed = stats["consumed"]
    wasted = stats["wasted"]

    green_score = 0

    if prepared > 0:
        green_score = round((consumed / prepared) * 100)

    conn.close()

    return render_template(
        "dashboard.html",
        meals=meals,
        inventory=inventory,
        surplus=surplus,
        prepared=prepared,
        consumed=consumed,
        wasted=wasted,
        green_score=green_score,
        today=date.today().isoformat()
    )


# ---------------- USER REGISTRATION ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "error"
            )
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, hashed_password))

            conn.commit()

            flash(
                "Registration successful! Please log in.",
                "success"
            )

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash(
                "This email is already registered.",
                "error"
            )

        finally:
            conn.close()

    return render_template("register.html")


# ---------------- USER LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session.clear()

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            flash(
                f"Welcome to MessMitra, {user['name']}!",
                "success"
            )

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# ---------------- USER LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have logged out successfully.",
        "success"
    )

    return redirect(url_for("login"))


# ---------------- ADD MEAL ----------------

@app.route("/add_meal", methods=["POST"])
def add_meal():

    meal_date = request.form.get("meal_date") or str(date.today())
    meal_type = request.form.get("meal_type", "").strip()
    menu = request.form.get("menu", "").strip()

    try:
        attendance = int(request.form.get("attendance", 0))
        prepared = int(request.form.get("prepared", 0))
        consumed = int(request.form.get("consumed", 0))

    except ValueError:

        flash(
            "Please enter valid numbers for meal quantities.",
            "error"
        )

        return redirect(url_for("dashboard"))

    if not meal_type or not menu:
        flash("Please enter the meal type and menu.", "error")
        return redirect(url_for("dashboard"))

    if min(attendance, prepared, consumed) < 0 or consumed > prepared:
        flash("Please check the meal quantities.", "error")
        return redirect(url_for("dashboard"))

    wasted = prepared - consumed

    conn = get_db()

    conn.execute("""
        INSERT INTO meals
        (meal_date, meal_type, menu, attendance, prepared, consumed, wasted)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        meal_date,
        meal_type,
        menu,
        attendance,
        prepared,
        consumed,
        wasted
    ))

    conn.commit()
    conn.close()

    flash("Meal record added successfully!", "success")

    return redirect(url_for("dashboard"))


# ---------------- AI FOOD PREDICTION ----------------

@app.route("/predict", methods=["POST"])
def predict():

    try:
        attendance = int(request.form.get("attendance", 0))

    except ValueError:
        return jsonify({
            "error": "Enter a valid attendance number."
        }), 400

    if attendance <= 0:
        return jsonify({
            "error": "Attendance must be greater than zero."
        }), 400

    conn = get_db()

    history = conn.execute("""
        SELECT attendance, prepared
        FROM meals
        WHERE attendance > 0 AND prepared > 0
        ORDER BY id DESC
        LIMIT 30
    """).fetchall()

    conn.close()

    if history:

        ratios = [
            row["prepared"] / row["attendance"]
            for row in history
        ]

        average_ratio = sum(ratios) / len(ratios)

    else:
        average_ratio = 1.05

    recommended = math.ceil(attendance * average_ratio)

    return jsonify({
        "attendance": attendance,
        "recommended": recommended,
        "message": f"Recommended preparation: {recommended} portions."
    })


# ---------------- ADD INVENTORY ----------------

@app.route("/add_inventory", methods=["POST"])
def add_inventory():

    item = request.form.get("item", "").strip()
    unit = request.form.get("unit", "").strip()
    expiry = request.form.get("expiry", "")

    try:
        quantity = float(request.form.get("quantity", 0))

    except ValueError:

        flash("Enter a valid inventory quantity.", "error")

        return redirect(url_for("dashboard"))

    if not item or not unit or quantity <= 0:
        flash("Enter valid inventory details.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db()

    conn.execute("""
        INSERT INTO inventory (item, quantity, unit, expiry)
        VALUES (?, ?, ?, ?)
    """, (item, quantity, unit, expiry))

    conn.commit()
    conn.close()

    flash("Inventory item added successfully!", "success")

    return redirect(url_for("dashboard"))


# ---------------- DELETE INVENTORY ----------------

@app.route("/delete_inventory/<int:item_id>", methods=["POST"])
def delete_inventory(item_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM inventory WHERE id = ?",
        (item_id,)
    )

    conn.commit()
    conn.close()

    flash("Inventory item deleted.", "success")

    return redirect(url_for("dashboard"))


# ---------------- ADD SURPLUS FOOD ----------------

@app.route("/add_surplus", methods=["POST"])
def add_surplus():

    food = request.form.get("food", "").strip()
    location = request.form.get("location", "").strip()
    unit = request.form.get("unit", "").strip()
    expiry = request.form.get("expiry", "")
    contact = request.form.get("contact", "").strip()

    try:
        quantity = float(request.form.get("quantity", 0))

    except ValueError:

        flash("Enter a valid surplus quantity.", "error")

        return redirect(url_for("dashboard"))

    if not food or not location or not unit or quantity <= 0:
        flash("Enter valid surplus food details.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db()

    conn.execute("""
        INSERT INTO surplus
        (food, quantity, unit, location, expiry, contact)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        food,
        quantity,
        unit,
        location,
        expiry,
        contact
    ))

    conn.commit()
    conn.close()

    flash("Surplus food listed successfully!", "success")

    return redirect(url_for("dashboard"))


# ---------------- CLAIM SURPLUS ----------------

@app.route("/claim_surplus/<int:surplus_id>", methods=["POST"])
def claim_surplus(surplus_id):

    conn = get_db()

    item = conn.execute(
        "SELECT * FROM surplus WHERE id = ?",
        (surplus_id,)
    ).fetchone()

    if item and item["status"] == "Available":

        conn.execute("""
            UPDATE surplus
            SET status = 'Claimed'
            WHERE id = ?
        """, (surplus_id,))

        flash("Surplus food claimed successfully!", "success")

    else:

        flash(
            "This food is no longer available.",
            "error"
        )

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


# ---------------- MITRA AI ASSISTANT ----------------

@app.route("/assistant", methods=["POST"])
def assistant():

    data = request.get_json(silent=True) or {}

    question = data.get("message", "").strip().lower()

    if not question:
        return jsonify({
            "answer": "Please enter a question."
        }), 400

    if any(word in question for word in ["waste", "food waste"]):

        answer = (
            "To reduce food waste, track daily attendance, "
            "use demand predictions, and list extra food on "
            "the Surplus Rescue Board."
        )

    elif any(word in question for word in ["inventory", "expiry"]):

        answer = (
            "Check your inventory expiry dates regularly. "
            "Use ingredients with the nearest expiry first."
        )

    elif any(word in question for word in ["predict", "quantity", "portions"]):

        answer = (
            "Use the AI Food Predictor. Enter expected attendance "
            "to estimate the number of portions to prepare."
        )

    elif any(word in question for word in ["surplus", "donate", "leftover"]):

        answer = (
            "Add excess food to the Surplus Rescue Board so "
            "other users can see and claim available food."
        )

    elif any(word in question for word in ["hello", "hi", "hey"]):

        answer = (
            "Hello! I'm Mitra, your MessMitra assistant. "
            "How can I help?"
        )

    else:

        answer = (
            "I'm Mitra! I can help with food waste, inventory, "
            "meal predictions, and surplus food management."
        )

    return jsonify({"answer": answer})


# ---------------- FOOD IMPACT ANALYTICS ----------------
@app.route("/analytics")
def analytics():

    conn = get_db()

    records = conn.execute("""
        SELECT
            meal_date,
            SUM(prepared) AS prepared,
            SUM(consumed) AS consumed,
            SUM(wasted) AS wasted
        FROM meals
        GROUP BY meal_date
        ORDER BY meal_date ASC
    """).fetchall()

    conn.close()

    dates = []
    prepared = []
    consumed = []
    wasted = []

    for row in records:
        dates.append(row["meal_date"])
        prepared.append(row["prepared"] or 0)
        consumed.append(row["consumed"] or 0)
        wasted.append(row["wasted"] or 0)

    total_prepared = sum(prepared)
    total_consumed = sum(consumed)
    total_wasted = sum(wasted)

    utilization = (
        (total_consumed / total_prepared) * 100
        if total_prepared > 0 else 0
    )

    waste_percentage = (
        (total_wasted / total_prepared) * 100
        if total_prepared > 0 else 0
    )

    green_score = max(0, min(100, 100 - waste_percentage))

    conn_data = {
        "dates": dates,
        "prepared": prepared,
        "consumed": consumed,
        "wasted": wasted,

        "total_prepared": total_prepared,
        "total_consumed": total_consumed,
        "total_wasted": total_wasted,

        "utilization": round(utilization, 2),
        "waste_percentage": round(waste_percentage, 2),
        "green_score": round(green_score, 2)
    }

    return jsonify(conn_data)

# ---------------- INVENTORY EXPIRY ALERTS ----------------

@app.route("/expiry_alerts")
def expiry_alerts():

    conn = get_db()

    items = conn.execute("""
        SELECT * FROM inventory
        WHERE expiry IS NOT NULL AND expiry != ''
        ORDER BY expiry ASC
    """).fetchall()

    conn.close()

    today = date.today()

    alerts = []

    for item in items:

        try:

            expiry_date = datetime.strptime(
                item["expiry"],
                "%Y-%m-%d"
            ).date()

            days_left = (expiry_date - today).days

            if days_left <= 3:

                alerts.append({
                    "item": item["item"],
                    "days_left": days_left,
                    "status": (
                        "Expired"
                        if days_left < 0
                        else "Expiring Soon"
                    )
                })

        except ValueError:
            continue

    return jsonify({"alerts": alerts})


# ---------------- START APPLICATION ----------------

if __name__ == "__main__":

    initialize_database()

    app.run(debug=True)
