"""Small Flask foundation for the manufacturing ERP.

This file intentionally starts with health and page routes. The business modules
will be added one at a time after the database schema is created and verified.
"""

import os
from io import BytesIO
from functools import wraps
from pathlib import Path
from urllib.parse import unquote, urlparse

import pymysql
import qrcode
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, send_file, send_from_directory, session, url_for
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from werkzeug.security import check_password_hash


PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")


def get_database_connection():
    """Create a MySQL connection from the DATABASE_URL environment value."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    # urlparse understands the URL structure, while unquote converts %40 back
    # to @ in the password before PyMySQL receives it.
    parsed_url = urlparse(database_url)
    return pymysql.connect(
        host=parsed_url.hostname or "localhost",
        port=parsed_url.port or 3306,
        user=unquote(parsed_url.username or ""),
        password=unquote(parsed_url.password or ""),
        database=parsed_url.path.lstrip("/"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def login_required(view_function):
    """Require a signed-in session before allowing a route to run."""
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "user" not in session:
            return jsonify({"error": "Authentication required."}), 401
        return view_function(*args, **kwargs)

    return wrapped_view


def role_required(*allowed_roles):
    """Require authentication plus one of the supplied ERP roles."""
    def decorator(view_function):
        @wraps(view_function)
        def wrapped_view(*args, **kwargs):
            user = session.get("user")
            if not user:
                return jsonify({"error": "Authentication required."}), 401
            if user["role"] not in allowed_roles:
                return jsonify({"error": "You do not have permission for this action."}), 403
            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Environment variables keep secrets and machine-specific settings out of code.
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY is not configured")
    app.config["SECRET_KEY"] = secret_key
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root@localhost/manufacturing_erp",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Database models and connection checks will be added after the MySQL
    # credentials are configured. Keeping this first slice independent makes
    # it possible to verify the Flask server before database integration.

    @app.get("/health")
    def health_check():
        """Return a small response used to verify that Flask is running."""
        return jsonify({"status": "ok", "service": "manufacturing-erp"})

    @app.get("/db-health")
    def database_health_check():
        """Confirm Flask can connect to MySQL and read seeded data."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS user_count FROM users")
                result = cursor.fetchone()
            return jsonify({"status": "ok", "database": "connected", **result})
        except Exception:
            # Do not expose connection strings or database credentials in errors.
            return jsonify({"status": "error", "database": "unavailable"}), 503
        finally:
            if connection is not None:
                connection.close()

    @app.post("/api/auth/login")
    def login_api():
        """Validate credentials against MySQL and create a server-side session."""
        data = request.get_json(silent=True) or {}
        username = str(data.get("username", "")).strip()
        password = str(data.get("password", ""))
        role = str(data.get("role", "")).strip()

        if not username or not password or not role:
            return jsonify({"error": "Username, password, and role are required."}), 400

        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, username, password_hash, role
                    FROM users
                    WHERE username = %s AND is_active = TRUE
                    """,
                    (username,),
                )
                user = cursor.fetchone()

            if not user or user["role"] != role or not check_password_hash(user["password_hash"], password):
                return jsonify({"error": "Invalid username, password, or role."}), 401

            # Flask signs this session with SECRET_KEY; the password is never stored.
            session["user"] = {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
            }
            return jsonify({"message": "Login successful", "user": session["user"]})
        except Exception:
            app.logger.exception("Login service failed while connecting to the database")
            return jsonify({"error": "Login service is unavailable."}), 503
        finally:
            if connection is not None:
                connection.close()

    @app.get("/api/auth/me")
    def current_user_api():
        """Return the current session user without exposing credentials."""
        user = session.get("user")
        if not user:
            return jsonify({"authenticated": False}), 401
        return jsonify({"authenticated": True, "user": user})

    @app.post("/api/auth/logout")
    def logout_api():
        """Clear the server-side login session."""
        session.clear()
        return jsonify({"message": "Logout successful"})

    @app.get("/api/products")
    @login_required
    def list_products_api():
        """Return active products, optionally filtered by a search term."""
        search_term = request.args.get("search", "").strip()
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, code, name, category, selling_price AS price, description
                    FROM products
                    WHERE is_active = TRUE
                      AND (code LIKE %s OR name LIKE %s OR category LIKE %s)
                    ORDER BY id
                    """,
                    tuple(f"%{search_term}%" for _ in range(3)),
                )
                return jsonify({"products": cursor.fetchall()})
        finally:
            if connection is not None:
                connection.close()

    @app.post("/api/products")
    @role_required("Administrator", "Manager")
    def create_product_api():
        """Create a product after validating its required fields."""
        data = request.get_json(silent=True) or {}
        code = str(data.get("code", "")).strip()
        name = str(data.get("name", "")).strip()
        category = str(data.get("category", "")).strip()
        description = str(data.get("description", "")).strip()

        try:
            price = float(data.get("price"))
        except (TypeError, ValueError):
            price = -1

        if not code or not name or not category or price < 0:
            return jsonify({"error": "Code, name, category, and a valid price are required."}), 400

        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO products (code, name, category, selling_price, description)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (code, name, category, price, description),
                )
                product_id = cursor.lastrowid
            return jsonify({"id": product_id, "message": "Product created."}), 201
        except pymysql.err.IntegrityError:
            return jsonify({"error": "Product code must be unique."}), 409
        finally:
            if connection is not None:
                connection.close()

    @app.put("/api/products/<int:product_id>")
    @role_required("Administrator", "Manager")
    def update_product_api(product_id):
        """Update an existing active product."""
        data = request.get_json(silent=True) or {}
        code = str(data.get("code", "")).strip()
        name = str(data.get("name", "")).strip()
        category = str(data.get("category", "")).strip()
        description = str(data.get("description", "")).strip()
        try:
            price = float(data.get("price"))
        except (TypeError, ValueError):
            price = -1

        if not code or not name or not category or price < 0:
            return jsonify({"error": "Code, name, category, and a valid price are required."}), 400

        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE products
                    SET code = %s, name = %s, category = %s, selling_price = %s, description = %s
                    WHERE id = %s AND is_active = TRUE
                    """,
                    (code, name, category, price, description, product_id),
                )
                if cursor.rowcount == 0:
                    return jsonify({"error": "Product not found."}), 404
            return jsonify({"message": "Product updated."})
        except pymysql.err.IntegrityError:
            return jsonify({"error": "Product code must be unique."}), 409
        finally:
            if connection is not None:
                connection.close()

    @app.delete("/api/products/<int:product_id>")
    @role_required("Administrator", "Manager")
    def deactivate_product_api(product_id):
        """Deactivate a product instead of deleting transaction history."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute("UPDATE products SET is_active = FALSE WHERE id = %s", (product_id,))
                if cursor.rowcount == 0:
                    return jsonify({"error": "Product not found."}), 404
            return jsonify({"message": "Product deactivated."})
        finally:
            if connection is not None:
                connection.close()

    @app.get("/api/materials")
    @login_required
    def list_materials_api():
        """Return materials with live quantities and calculated stock status."""
        search_term = request.args.get("search", "").strip()
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT material.id, material.code, material.name, material.category,
                           material.unit, material.minimum_stock,
                           COALESCE(inventory.quantity, 0) AS quantity,
                           supplier.name AS supplier_name
                    FROM materials material
                    LEFT JOIN inventory ON inventory.material_id = material.id
                    LEFT JOIN suppliers supplier ON supplier.id = material.supplier_id
                    WHERE material.is_active = TRUE
                      AND (material.code LIKE %s OR material.name LIKE %s OR material.category LIKE %s)
                    ORDER BY material.id
                    """,
                    tuple(f"%{search_term}%" for _ in range(3)),
                )
                materials = cursor.fetchall()
            for material in materials:
                material["status"] = (
                    "Low Stock"
                    if float(material["quantity"]) <= float(material["minimum_stock"])
                    else "Available"
                )
            return jsonify({"materials": materials})
        finally:
            if connection is not None:
                connection.close()

    @app.post("/api/materials")
    @role_required("Administrator", "Manager")
    def create_material_api():
        """Create a material and its initial inventory row."""
        data = request.get_json(silent=True) or {}
        code = str(data.get("code", "")).strip()
        name = str(data.get("name", "")).strip()
        category = str(data.get("category", "")).strip()
        unit = str(data.get("unit", "")).strip()
        supplier_id = data.get("supplier_id")
        try:
            minimum_stock = float(data.get("minimum_stock"))
            quantity = float(data.get("quantity", 0))
        except (TypeError, ValueError):
            minimum_stock = -1
            quantity = -1

        if not code or not name or not category or not unit or minimum_stock < 0 or quantity < 0:
            return jsonify({"error": "Material fields and non-negative quantities are required."}), 400

        connection = None
        try:
            connection = get_database_connection()
            connection.begin()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO materials (code, name, category, unit, minimum_stock, supplier_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (code, name, category, unit, minimum_stock, supplier_id or None),
                )
                material_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO inventory (material_id, quantity) VALUES (%s, %s)",
                    (material_id, quantity),
                )
            connection.commit()
            return jsonify({"id": material_id, "message": "Material created."}), 201
        except pymysql.err.IntegrityError:
            if connection is not None:
                connection.rollback()
            return jsonify({"error": "Material code must be unique and supplier must exist."}), 409
        finally:
            if connection is not None:
                connection.close()

    @app.delete("/api/materials/<int:material_id>")
    @role_required("Administrator", "Manager")
    def deactivate_material_api(material_id):
        """Deactivate a material while preserving its inventory history."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute("UPDATE materials SET is_active = FALSE WHERE id = %s", (material_id,))
                if cursor.rowcount == 0:
                    return jsonify({"error": "Material not found."}), 404
            return jsonify({"message": "Material deactivated."})
        finally:
            if connection is not None:
                connection.close()

    @app.get("/api/suppliers")
    @login_required
    def list_suppliers_api():
        """Return active suppliers, optionally filtered by search text."""
        search_term = request.args.get("search", "").strip()
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, code, name, phone, email, address
                    FROM suppliers
                    WHERE is_active = TRUE
                      AND (code LIKE %s OR name LIKE %s OR email LIKE %s)
                    ORDER BY id
                    """,
                    tuple(f"%{search_term}%" for _ in range(3)),
                )
                return jsonify({"suppliers": cursor.fetchall()})
        finally:
            if connection is not None:
                connection.close()

    @app.post("/api/suppliers")
    @role_required("Administrator", "Manager")
    def create_supplier_api():
        """Create a supplier after validating required contact fields."""
        data = request.get_json(silent=True) or {}
        values = {
            "code": str(data.get("code", "")).strip(),
            "name": str(data.get("name", "")).strip(),
            "phone": str(data.get("phone", "")).strip(),
            "email": str(data.get("email", "")).strip(),
            "address": str(data.get("address", "")).strip(),
        }
        if not all(values.values()):
            return jsonify({"error": "All supplier fields are required."}), 400

        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO suppliers (code, name, phone, email, address)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    tuple(values.values()),
                )
                supplier_id = cursor.lastrowid
            return jsonify({"id": supplier_id, "message": "Supplier created."}), 201
        except pymysql.err.IntegrityError:
            return jsonify({"error": "Supplier code must be unique."}), 409
        finally:
            if connection is not None:
                connection.close()

    @app.put("/api/suppliers/<int:supplier_id>")
    @role_required("Administrator", "Manager")
    def update_supplier_api(supplier_id):
        """Update an active supplier."""
        data = request.get_json(silent=True) or {}
        values = (
            str(data.get("code", "")).strip(),
            str(data.get("name", "")).strip(),
            str(data.get("phone", "")).strip(),
            str(data.get("email", "")).strip(),
            str(data.get("address", "")).strip(),
        )
        if not all(values):
            return jsonify({"error": "All supplier fields are required."}), 400

        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE suppliers
                    SET code = %s, name = %s, phone = %s, email = %s, address = %s
                    WHERE id = %s AND is_active = TRUE
                    """,
                    (*values, supplier_id),
                )
                if cursor.rowcount == 0:
                    return jsonify({"error": "Supplier not found."}), 404
            return jsonify({"message": "Supplier updated."})
        except pymysql.err.IntegrityError:
            return jsonify({"error": "Supplier code must be unique."}), 409
        finally:
            if connection is not None:
                connection.close()

    @app.delete("/api/suppliers/<int:supplier_id>")
    @role_required("Administrator", "Manager")
    def deactivate_supplier_api(supplier_id):
        """Deactivate a supplier without deleting purchase history."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute("UPDATE suppliers SET is_active = FALSE WHERE id = %s", (supplier_id,))
                if cursor.rowcount == 0:
                    return jsonify({"error": "Supplier not found."}), 404
            return jsonify({"message": "Supplier deactivated."})
        finally:
            if connection is not None:
                connection.close()

    @app.get("/api/purchases")
    @login_required
    def list_purchases_api():
        """Return purchase orders with their supplier and material details."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT purchase.id, purchase.order_number, purchase.status,
                           purchase.order_date, supplier.name AS supplier_name,
                           item.material_id, material.name AS material_name,
                           item.quantity, item.unit_price,
                           item.quantity * item.unit_price AS total
                    FROM purchase_orders purchase
                    JOIN suppliers supplier ON supplier.id = purchase.supplier_id
                    JOIN purchase_order_items item ON item.purchase_order_id = purchase.id
                    JOIN materials material ON material.id = item.material_id
                    ORDER BY purchase.id DESC
                    """
                )
                return jsonify({"purchases": cursor.fetchall()})
        finally:
            if connection is not None:
                connection.close()

    @app.post("/api/purchases")
    @login_required
    def create_purchase_api():
        """Create an Ordered purchase without changing inventory."""
        data = request.get_json(silent=True) or {}
        try:
            supplier_id = int(data.get("supplier_id"))
            material_id = int(data.get("material_id"))
            quantity = float(data.get("quantity"))
            unit_price = float(data.get("unit_price"))
        except (TypeError, ValueError):
            return jsonify({"error": "Supplier, material, quantity, and price are required."}), 400

        if quantity <= 0 or unit_price < 0:
            return jsonify({"error": "Quantity must be positive and price cannot be negative."}), 400

        connection = None
        try:
            connection = get_database_connection()
            connection.begin()
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM suppliers WHERE id = %s AND is_active = TRUE", (supplier_id,))
                if not cursor.fetchone():
                    return jsonify({"error": "Supplier not found."}), 404
                cursor.execute("SELECT id FROM materials WHERE id = %s AND is_active = TRUE", (material_id,))
                if not cursor.fetchone():
                    return jsonify({"error": "Material not found."}), 404
                order_number = f"PO-{os.urandom(4).hex().upper()}"
                cursor.execute(
                    """
                    INSERT INTO purchase_orders (order_number, supplier_id, status, order_date, created_by)
                    VALUES (%s, %s, 'Ordered', CURDATE(), %s)
                    """,
                    (order_number, supplier_id, session["user"]["id"]),
                )
                purchase_id = cursor.lastrowid
                cursor.execute(
                    """
                    INSERT INTO purchase_order_items (purchase_order_id, material_id, quantity, unit_price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (purchase_id, material_id, quantity, unit_price),
                )
            connection.commit()
            return jsonify({"id": purchase_id, "order_number": order_number}), 201
        except pymysql.err.IntegrityError:
            if connection is not None:
                connection.rollback()
            return jsonify({"error": "Purchase data is invalid."}), 400
        finally:
            if connection is not None:
                connection.close()

    @app.post("/api/purchases/<int:purchase_id>/receive")
    @login_required
    def receive_purchase_api(purchase_id):
        """Receive a purchase once and increase its material inventory atomically."""
        connection = None
        try:
            connection = get_database_connection()
            connection.begin()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT purchase.status, item.material_id, item.quantity
                    FROM purchase_orders purchase
                    JOIN purchase_order_items item ON item.purchase_order_id = purchase.id
                    WHERE purchase.id = %s
                    FOR UPDATE
                    """,
                    (purchase_id,),
                )
                purchase = cursor.fetchone()
                if not purchase:
                    connection.rollback()
                    return jsonify({"error": "Purchase order not found."}), 404
                if purchase["status"] != "Ordered":
                    connection.rollback()
                    return jsonify({"error": "Only Ordered purchases can be received."}), 409

                cursor.execute(
                    "UPDATE inventory SET quantity = quantity + %s WHERE material_id = %s",
                    (purchase["quantity"], purchase["material_id"]),
                )
                cursor.execute(
                    """
                    INSERT INTO stock_movements
                        (material_id, quantity_change, reason, source_type, source_id, created_by)
                    VALUES (%s, %s, 'Purchase Receipt', 'purchase_order', %s, %s)
                    """,
                    (purchase["material_id"], purchase["quantity"], purchase_id, session["user"]["id"]),
                )
                cursor.execute(
                    """
                    UPDATE purchase_orders
                    SET status = 'Received', received_at = NOW()
                    WHERE id = %s
                    """,
                    (purchase_id,),
                )
                cursor.execute(
                    """
                    INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details)
                    VALUES (%s, 'Material Receipt', 'purchase_order', %s, %s)
                    """,
                    (session["user"]["id"], purchase_id, '{"inventory_updated": true}'),
                )
            connection.commit()
            return jsonify({"message": "Material received and inventory updated."})
        except Exception:
            if connection is not None:
                connection.rollback()
            return jsonify({"error": "Material receipt failed."}), 500
        finally:
            if connection is not None:
                connection.close()

    @app.get("/api/boms")
    @login_required
    def list_boms_api():
        """Return each product BOM with its required materials."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT bom.id AS bom_id, product.id AS product_id, product.name AS product_name,
                           material.id AS material_id, material.name AS material_name,
                           material.unit, item.quantity_per_unit
                    FROM bom_headers bom
                    JOIN products product ON product.id = bom.product_id
                    JOIN bom_items item ON item.bom_id = bom.id
                    JOIN materials material ON material.id = item.material_id
                    WHERE bom.is_active = TRUE AND product.is_active = TRUE
                    ORDER BY product.id, item.id
                    """
                )
                return jsonify({"boms": cursor.fetchall()})
        finally:
            if connection is not None:
                connection.close()

    @app.post("/api/boms")
    @role_required("Administrator", "Manager")
    def save_bom_api():
        """Create or replace a product BOM with validated material quantities."""
        data = request.get_json(silent=True) or {}
        try:
            product_id = int(data.get("product_id"))
            items = data.get("items", [])
        except (TypeError, ValueError):
            return jsonify({"error": "Product and BOM items are required."}), 400
        if not items or not isinstance(items, list):
            return jsonify({"error": "Add at least one BOM material."}), 400

        normalized_items = []
        seen_materials = set()
        for item in items:
            try:
                material_id = int(item["material_id"])
                quantity_per_unit = float(item["quantity_per_unit"])
            except (KeyError, TypeError, ValueError):
                return jsonify({"error": "Each BOM item needs a material and quantity."}), 400
            if quantity_per_unit <= 0 or material_id in seen_materials:
                return jsonify({"error": "BOM quantities must be positive and materials cannot repeat."}), 400
            seen_materials.add(material_id)
            normalized_items.append((material_id, quantity_per_unit))

        connection = None
        try:
            connection = get_database_connection()
            connection.begin()
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM products WHERE id=%s AND is_active=TRUE", (product_id,))
                if not cursor.fetchone():
                    connection.rollback()
                    return jsonify({"error": "Product not found."}), 404
                for material_id, _ in normalized_items:
                    cursor.execute("SELECT id FROM materials WHERE id=%s AND is_active=TRUE", (material_id,))
                    if not cursor.fetchone():
                        connection.rollback()
                        return jsonify({"error": "One or more materials were not found."}), 404
                cursor.execute("SELECT id FROM bom_headers WHERE product_id=%s", (product_id,))
                bom = cursor.fetchone()
                if bom:
                    bom_id = bom["id"]
                    cursor.execute("DELETE FROM bom_items WHERE bom_id=%s", (bom_id,))
                else:
                    cursor.execute("INSERT INTO bom_headers (product_id) VALUES (%s)", (product_id,))
                    bom_id = cursor.lastrowid
                cursor.executemany(
                    "INSERT INTO bom_items (bom_id, material_id, quantity_per_unit) VALUES (%s,%s,%s)",
                    [(bom_id, material_id, quantity) for material_id, quantity in normalized_items],
                )
            connection.commit()
            return jsonify({"bom_id": bom_id, "message": "BOM saved."}), 201
        except Exception:
            if connection is not None:
                connection.rollback()
            return jsonify({"error": "BOM could not be saved."}), 500
        finally:
            if connection is not None:
                connection.close()

    @app.get("/api/production")
    @login_required
    def list_production_api():
        """Return production orders and their current statuses."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT production.id, production.order_number, production.product_id,
                           product.name AS product_name, production.quantity, production.status,
                           production.created_at, production.completed_at
                    FROM production_orders production
                    JOIN products product ON product.id = production.product_id
                    ORDER BY production.id DESC
                    """
                )
                return jsonify({"orders": cursor.fetchall()})
        finally:
            if connection is not None:
                connection.close()

    @app.post("/api/production")
    @login_required
    def create_production_api():
        """Create a pending production order after checking its BOM stock."""
        data = request.get_json(silent=True) or {}
        try:
            product_id = int(data.get("product_id"))
            quantity = float(data.get("quantity"))
        except (TypeError, ValueError):
            return jsonify({"error": "Product and quantity are required."}), 400
        if quantity <= 0:
            return jsonify({"error": "Production quantity must be positive."}), 400

        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT item.material_id, item.quantity_per_unit, material.name AS material_name,
                           COALESCE(inventory.quantity, 0) AS available
                    FROM bom_headers bom
                    JOIN bom_items item ON item.bom_id = bom.id
                    JOIN materials material ON material.id = item.material_id
                    LEFT JOIN inventory ON inventory.material_id = item.material_id
                    WHERE bom.product_id = %s AND bom.is_active = TRUE
                    """,
                    (product_id,),
                )
                requirements = cursor.fetchall()
                if not requirements:
                    return jsonify({"error": "This product has no active BOM."}), 400
                insufficient = next(
                    (item for item in requirements if float(item["available"]) < float(item["quantity_per_unit"]) * quantity),
                    None,
                )
                if insufficient:
                    return jsonify({"error": f"Insufficient {insufficient['material_name']} stock."}), 409
                order_number = f"PROD-{os.urandom(4).hex().upper()}"
                cursor.execute(
                    """
                    INSERT INTO production_orders (order_number, product_id, quantity, status, created_by)
                    VALUES (%s, %s, %s, 'Pending', %s)
                    """,
                    (order_number, product_id, quantity, session["user"]["id"]),
                )
                return jsonify({"id": cursor.lastrowid, "order_number": order_number}), 201
        finally:
            if connection is not None:
                connection.close()

    @app.post("/api/production/<int:production_id>/start")
    @login_required
    def start_production_api(production_id):
        """Move a pending production order into progress."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE production_orders SET status = 'In Progress' WHERE id = %s AND status = 'Pending'",
                    (production_id,),
                )
                if cursor.rowcount == 0:
                    return jsonify({"error": "Only Pending production can be started."}), 409
            return jsonify({"message": "Production started."})
        finally:
            if connection is not None:
                connection.close()

    @app.post("/api/production/<int:production_id>/complete")
    @login_required
    def complete_production_api(production_id):
        """Consume BOM materials and add finished goods atomically."""
        connection = None
        try:
            connection = get_database_connection()
            connection.begin()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT product_id, quantity, status FROM production_orders WHERE id = %s FOR UPDATE",
                    (production_id,),
                )
                order = cursor.fetchone()
                if not order or order["status"] != "In Progress":
                    connection.rollback()
                    return jsonify({"error": "Only In Progress production can be completed."}), 409
                cursor.execute(
                    """
                    SELECT item.material_id, item.quantity_per_unit, COALESCE(inventory.quantity, 0) AS available
                    FROM bom_headers bom
                    JOIN bom_items item ON item.bom_id = bom.id
                    LEFT JOIN inventory ON inventory.material_id = item.material_id
                    WHERE bom.product_id = %s AND bom.is_active = TRUE
                    FOR UPDATE
                    """,
                    (order["product_id"],),
                )
                requirements = cursor.fetchall()
                for item in requirements:
                    amount = float(item["quantity_per_unit"]) * float(order["quantity"])
                    if float(item["available"]) < amount:
                        connection.rollback()
                        return jsonify({"error": "Raw material stock is no longer sufficient."}), 409
                    cursor.execute(
                        "UPDATE inventory SET quantity = quantity - %s WHERE material_id = %s",
                        (amount, item["material_id"]),
                    )
                    cursor.execute(
                        """
                        INSERT INTO stock_movements
                            (material_id, quantity_change, reason, source_type, source_id, created_by)
                        VALUES (%s, %s, 'Production Consumption', 'production_order', %s, %s)
                        """,
                        (item["material_id"], -amount, production_id, session["user"]["id"]),
                    )
                cursor.execute(
                    "UPDATE inventory SET quantity = quantity + %s WHERE product_id = %s",
                    (order["quantity"], order["product_id"]),
                )
                cursor.execute(
                    """
                    INSERT INTO stock_movements
                        (product_id, quantity_change, reason, source_type, source_id, created_by)
                    VALUES (%s, %s, 'Production Output', 'production_order', %s, %s)
                    """,
                    (order["product_id"], order["quantity"], production_id, session["user"]["id"]),
                )
                cursor.execute(
                    "UPDATE production_orders SET status = 'Completed', completed_at = NOW() WHERE id = %s",
                    (production_id,),
                )
                cursor.execute(
                    """
                    INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details)
                    VALUES (%s, 'Production Completion', 'production_order', %s, %s)
                    """,
                    (session["user"]["id"], production_id, '{"inventory_updated": true}'),
                )
            connection.commit()
            return jsonify({"message": "Production completed and inventory updated."})
        except Exception:
            if connection is not None:
                connection.rollback()
            return jsonify({"error": "Production completion failed."}), 500
        finally:
            if connection is not None:
                connection.close()

    @app.get("/api/customers")
    @login_required
    def list_customers_api():
        """Return active customers, optionally filtered by search text."""
        search_term = request.args.get("search", "").strip()
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, code, name, phone, email, address
                    FROM customers
                    WHERE is_active = TRUE
                      AND (code LIKE %s OR name LIKE %s OR email LIKE %s)
                    ORDER BY id
                    """,
                    tuple(f"%{search_term}%" for _ in range(3)),
                )
                return jsonify({"customers": cursor.fetchall()})
        finally:
            if connection is not None:
                connection.close()

    @app.post("/api/customers")
    @role_required("Administrator", "Manager")
    def create_customer_api():
        """Create a customer after validating contact information."""
        data = request.get_json(silent=True) or {}
        values = (
            str(data.get("code", "")).strip(),
            str(data.get("name", "")).strip(),
            str(data.get("phone", "")).strip(),
            str(data.get("email", "")).strip(),
            str(data.get("address", "")).strip(),
        )
        if not all(values):
            return jsonify({"error": "All customer fields are required."}), 400
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO customers (code, name, phone, email, address) VALUES (%s, %s, %s, %s, %s)",
                    values,
                )
                return jsonify({"id": cursor.lastrowid, "message": "Customer created."}), 201
        except pymysql.err.IntegrityError:
            return jsonify({"error": "Customer code must be unique."}), 409
        finally:
            if connection is not None:
                connection.close()

    @app.put("/api/customers/<int:customer_id>")
    @role_required("Administrator", "Manager")
    def update_customer_api(customer_id):
        """Update an active customer."""
        data = request.get_json(silent=True) or {}
        values = (
            str(data.get("code", "")).strip(),
            str(data.get("name", "")).strip(),
            str(data.get("phone", "")).strip(),
            str(data.get("email", "")).strip(),
            str(data.get("address", "")).strip(),
        )
        if not all(values):
            return jsonify({"error": "All customer fields are required."}), 400
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE customers SET code=%s, name=%s, phone=%s, email=%s, address=%s
                    WHERE id=%s AND is_active=TRUE
                    """,
                    (*values, customer_id),
                )
                if cursor.rowcount == 0:
                    return jsonify({"error": "Customer not found."}), 404
            return jsonify({"message": "Customer updated."})
        except pymysql.err.IntegrityError:
            return jsonify({"error": "Customer code must be unique."}), 409
        finally:
            if connection is not None:
                connection.close()

    @app.delete("/api/customers/<int:customer_id>")
    @role_required("Administrator", "Manager")
    def deactivate_customer_api(customer_id):
        """Deactivate a customer without deleting sales history."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute("UPDATE customers SET is_active=FALSE WHERE id=%s", (customer_id,))
                if cursor.rowcount == 0:
                    return jsonify({"error": "Customer not found."}), 404
            return jsonify({"message": "Customer deactivated."})
        finally:
            if connection is not None:
                connection.close()

    @app.get("/api/sales")
    @login_required
    def list_sales_api():
        """Return sales orders with customer and product details."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT sale.id, sale.order_number, sale.status, sale.order_date,
                           customer.name AS customer_name, item.product_id,
                           product.name AS product_name, item.quantity, item.unit_price,
                           item.quantity * item.unit_price AS total
                    FROM sales_orders sale
                    JOIN customers customer ON customer.id=sale.customer_id
                    JOIN sales_order_items item ON item.sales_order_id=sale.id
                    JOIN products product ON product.id=item.product_id
                    ORDER BY sale.id DESC
                    """
                )
                return jsonify({"sales": cursor.fetchall()})
        finally:
            if connection is not None:
                connection.close()

    @app.post("/api/sales")
    @login_required
    def create_sale_api():
        """Create a pending sale only when enough finished stock exists."""
        data = request.get_json(silent=True) or {}
        try:
            customer_id = int(data.get("customer_id"))
            product_id = int(data.get("product_id"))
            quantity = float(data.get("quantity"))
            unit_price = float(data.get("unit_price"))
        except (TypeError, ValueError):
            return jsonify({"error": "Customer, product, quantity, and price are required."}), 400
        if quantity <= 0 or unit_price < 0:
            return jsonify({"error": "Quantity must be positive and price cannot be negative."}), 400

        connection = None
        try:
            connection = get_database_connection()
            connection.begin()
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM customers WHERE id=%s AND is_active=TRUE", (customer_id,))
                if not cursor.fetchone():
                    connection.rollback()
                    return jsonify({"error": "Customer not found."}), 404
                cursor.execute(
                    "SELECT id, quantity FROM inventory WHERE product_id=%s FOR UPDATE",
                    (product_id,),
                )
                inventory = cursor.fetchone()
                if not inventory or float(inventory["quantity"]) < quantity:
                    connection.rollback()
                    return jsonify({"error": "Insufficient finished-product stock."}), 409
                order_number = f"SO-{os.urandom(4).hex().upper()}"
                cursor.execute(
                    """
                    INSERT INTO sales_orders (order_number, customer_id, status, order_date, created_by)
                    VALUES (%s, %s, 'Pending', CURDATE(), %s)
                    """,
                    (order_number, customer_id, session["user"]["id"]),
                )
                sale_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO sales_order_items (sales_order_id, product_id, quantity, unit_price) VALUES (%s,%s,%s,%s)",
                    (sale_id, product_id, quantity, unit_price),
                )
            connection.commit()
            return jsonify({"id": sale_id, "order_number": order_number}), 201
        except pymysql.err.IntegrityError:
            if connection is not None:
                connection.rollback()
            return jsonify({"error": "Sales data is invalid."}), 400
        finally:
            if connection is not None:
                connection.close()

    @app.post("/api/sales/<int:sale_id>/process")
    @login_required
    def process_sale_api(sale_id):
        """Reduce finished inventory and mark a sale Processed atomically."""
        connection = None
        try:
            connection = get_database_connection()
            connection.begin()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT sale.status, item.product_id, item.quantity
                    FROM sales_orders sale
                    JOIN sales_order_items item ON item.sales_order_id=sale.id
                    WHERE sale.id=%s FOR UPDATE
                    """,
                    (sale_id,),
                )
                sale = cursor.fetchone()
                if not sale or sale["status"] != "Pending":
                    connection.rollback()
                    return jsonify({"error": "Only Pending sales can be processed."}), 409
                cursor.execute(
                    "SELECT quantity FROM inventory WHERE product_id=%s FOR UPDATE",
                    (sale["product_id"],),
                )
                inventory = cursor.fetchone()
                if not inventory or float(inventory["quantity"]) < float(sale["quantity"]):
                    connection.rollback()
                    return jsonify({"error": "Finished-product stock is no longer sufficient."}), 409
                cursor.execute(
                    "UPDATE inventory SET quantity=quantity-%s WHERE product_id=%s",
                    (sale["quantity"], sale["product_id"]),
                )
                cursor.execute(
                    """
                    INSERT INTO stock_movements
                        (product_id, quantity_change, reason, source_type, source_id, created_by)
                    VALUES (%s, %s, 'Sales Processing', 'sales_order', %s, %s)
                    """,
                    (sale["product_id"], -sale["quantity"], sale_id, session["user"]["id"]),
                )
                cursor.execute("UPDATE sales_orders SET status='Processed', processed_at=NOW() WHERE id=%s", (sale_id,))
                cursor.execute(
                    """
                    INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details)
                    VALUES (%s, 'Sale Processing', 'sales_order', %s, %s)
                    """,
                    (session["user"]["id"], sale_id, '{"inventory_updated": true}'),
                )
            connection.commit()
            return jsonify({"message": "Sale processed and inventory updated."})
        except Exception:
            if connection is not None:
                connection.rollback()
            return jsonify({"error": "Sale processing failed."}), 500
        finally:
            if connection is not None:
                connection.close()

    @app.get("/api/audit-logs")
    @login_required
    def list_audit_logs_api():
        """Return recent business actions for the audit-log screen."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT audit.id, audit.action, audit.entity_type, audit.entity_id,
                           audit.details, audit.created_at, user.username
                    FROM audit_logs audit
                    JOIN users user ON user.id = audit.user_id
                    ORDER BY audit.id DESC
                    LIMIT 100
                    """
                )
                return jsonify({"logs": cursor.fetchall()})
        finally:
            if connection is not None:
                connection.close()

    @app.get("/api/notifications")
    @login_required
    def list_notifications_api():
        """Generate and return current low-stock notifications for the user."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT material.id, material.name, material.minimum_stock,
                           COALESCE(inventory.quantity, 0) AS quantity
                    FROM materials material
                    LEFT JOIN inventory ON inventory.material_id=material.id
                    WHERE material.is_active=TRUE
                      AND COALESCE(inventory.quantity, 0) <= material.minimum_stock
                    """
                )
                low_stock_items = cursor.fetchall()
                for item in low_stock_items:
                    title = f"Low stock: {item['name']}"
                    message = f"Current quantity is {item['quantity']}; minimum is {item['minimum_stock']}."
                    # Avoid creating the same unread alert repeatedly on refresh.
                    cursor.execute(
                        """
                        SELECT id FROM notifications
                        WHERE user_id=%s AND title=%s AND is_read=FALSE
                        LIMIT 1
                        """,
                        (session["user"]["id"], title),
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            """
                            INSERT INTO notifications (user_id, title, message)
                            VALUES (%s, %s, %s)
                            """,
                            (session["user"]["id"], title, message),
                        )
                cursor.execute(
                    """
                    SELECT id, title, message, is_read, created_at
                    FROM notifications
                    WHERE user_id=%s
                    ORDER BY id DESC
                    LIMIT 50
                    """,
                    (session["user"]["id"],),
                )
                notifications = cursor.fetchall()
            return jsonify({"notifications": notifications})
        finally:
            if connection is not None:
                connection.close()

    @app.post("/api/notifications/<int:notification_id>/read")
    @login_required
    def mark_notification_read_api(notification_id):
        """Mark one notification as read for the current user."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE notifications SET is_read=TRUE WHERE id=%s AND user_id=%s",
                    (notification_id, session["user"]["id"]),
                )
                if cursor.rowcount == 0:
                    return jsonify({"error": "Notification not found."}), 404
            return jsonify({"message": "Notification marked as read."})
        finally:
            if connection is not None:
                connection.close()

    @app.get("/api/exports/inventory.xlsx")
    @login_required
    def export_inventory_excel():
        """Export current raw-material inventory as an Excel workbook."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT material.code, material.name, material.category, material.unit,
                           COALESCE(inventory.quantity, 0) AS quantity, material.minimum_stock,
                           CASE WHEN COALESCE(inventory.quantity,0) <= material.minimum_stock
                                THEN 'Low Stock' ELSE 'Available' END AS status
                    FROM materials material
                    LEFT JOIN inventory ON inventory.material_id=material.id
                    WHERE material.is_active=TRUE ORDER BY material.id
                    """
                )
                rows = cursor.fetchall()
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Inventory"
            headers = ["Code", "Material", "Category", "Unit", "Quantity", "Minimum Stock", "Status"]
            sheet.append(headers)
            for row in rows:
                sheet.append([row["code"], row["name"], row["category"], row["unit"], row["quantity"], row["minimum_stock"], row["status"]])
            output = BytesIO()
            workbook.save(output)
            output.seek(0)
            return send_file(output, as_attachment=True, download_name="inventory.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        finally:
            if connection is not None:
                connection.close()

    @app.get("/api/sales/<int:sale_id>/invoice.pdf")
    @login_required
    def sales_invoice_pdf(sale_id):
        """Generate a simple PDF invoice for a sales order."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT sale.order_number, sale.order_date, sale.status,
                           customer.name AS customer_name, customer.email, customer.address,
                           product.name AS product_name, item.quantity, item.unit_price,
                           item.quantity * item.unit_price AS total
                    FROM sales_orders sale
                    JOIN customers customer ON customer.id=sale.customer_id
                    JOIN sales_order_items item ON item.sales_order_id=sale.id
                    JOIN products product ON product.id=item.product_id
                    WHERE sale.id=%s
                    """,
                    (sale_id,),
                )
                sale = cursor.fetchone()
            if not sale:
                return jsonify({"error": "Sales order not found."}), 404
            output = BytesIO()
            document = canvas.Canvas(output, pagesize=A4)
            document.setTitle(f"Invoice {sale['order_number']}")
            document.setFont("Helvetica-Bold", 18)
            document.drawString(60, 790, "Manufacturing ERP Invoice")
            document.setFont("Helvetica", 11)
            document.drawString(60, 755, f"Invoice: {sale['order_number']}")
            document.drawString(60, 738, f"Date: {sale['order_date']}")
            document.drawString(60, 700, f"Customer: {sale['customer_name']}")
            document.drawString(60, 683, f"Email: {sale['email']}")
            document.drawString(60, 666, f"Address: {sale['address']}")
            document.line(60, 640, 535, 640)
            document.drawString(60, 615, "Product")
            document.drawString(320, 615, "Quantity")
            document.drawString(410, 615, "Unit Price")
            document.drawString(490, 615, "Total")
            document.drawString(60, 590, sale["product_name"])
            document.drawString(320, 590, str(sale["quantity"]))
            document.drawString(410, 590, f"Rs. {float(sale['unit_price']):.2f}")
            document.drawString(490, 590, f"Rs. {float(sale['total']):.2f}")
            document.line(60, 565, 535, 565)
            document.setFont("Helvetica-Bold", 13)
            document.drawString(390, 535, f"Grand Total: Rs. {float(sale['total']):.2f}")
            document.save()
            output.seek(0)
            return send_file(output, as_attachment=True, download_name=f"invoice-{sale['order_number']}.pdf", mimetype="application/pdf")
        finally:
            if connection is not None:
                connection.close()

    @app.get("/api/products/<int:product_id>/qr.png")
    @login_required
    def product_qr_code(product_id):
        """Generate a QR code containing a product reference."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT code, name FROM products WHERE id=%s AND is_active=TRUE", (product_id,))
                product = cursor.fetchone()
            if not product:
                return jsonify({"error": "Product not found."}), 404
            image = qrcode.make(f"Product: {product['code']} | {product['name']}")
            output = BytesIO()
            image.save(output, format="PNG")
            output.seek(0)
            return send_file(output, mimetype="image/png", download_name=f"{product['code']}.png")
        finally:
            if connection is not None:
                connection.close()

    @app.get("/api/dashboard/summary")
    @login_required
    def dashboard_summary_api():
        """Return live KPI cards and chart data for the dashboard."""
        connection = None
        try:
            connection = get_database_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS total_products FROM products WHERE is_active=TRUE")
                total_products = cursor.fetchone()["total_products"]
                cursor.execute("SELECT COUNT(*) AS total_materials FROM materials WHERE is_active=TRUE")
                total_materials = cursor.fetchone()["total_materials"]
                cursor.execute(
                    """
                    SELECT COUNT(*) AS low_stock
                    FROM materials material
                    LEFT JOIN inventory ON inventory.material_id=material.id
                    WHERE material.is_active=TRUE
                      AND COALESCE(inventory.quantity,0) <= material.minimum_stock
                    """
                )
                low_stock = cursor.fetchone()["low_stock"]
                cursor.execute("SELECT COUNT(*) AS pending_purchases FROM purchase_orders WHERE status IN ('Draft','Ordered')")
                pending_purchases = cursor.fetchone()["pending_purchases"]
                cursor.execute("SELECT COUNT(*) AS active_production FROM production_orders WHERE status='In Progress'")
                active_production = cursor.fetchone()["active_production"]
                cursor.execute("SELECT COUNT(*) AS completed_production FROM production_orders WHERE status='Completed'")
                completed_production = cursor.fetchone()["completed_production"]
                cursor.execute("SELECT COUNT(*) AS pending_sales FROM sales_orders WHERE status='Pending'")
                pending_sales = cursor.fetchone()["pending_sales"]
                cursor.execute("SELECT COUNT(*) AS customers FROM customers WHERE is_active=TRUE")
                customers = cursor.fetchone()["customers"]
                cursor.execute("SELECT COUNT(*) AS suppliers FROM suppliers WHERE is_active=TRUE")
                suppliers = cursor.fetchone()["suppliers"]
                cursor.execute(
                    """
                    SELECT
                        SUM(CASE WHEN quantity > minimum_stock THEN 1 ELSE 0 END) AS available,
                        SUM(CASE WHEN quantity <= minimum_stock THEN 1 ELSE 0 END) AS low_stock
                    FROM materials material
                    LEFT JOIN inventory ON inventory.material_id=material.id
                    WHERE material.is_active=TRUE
                    """
                )
                inventory_chart = cursor.fetchone()
                cursor.execute(
                    "SELECT status, COUNT(*) AS count FROM production_orders GROUP BY status ORDER BY status"
                )
                production_chart = cursor.fetchall()
                cursor.execute(
                    """
                    SELECT order_date AS period, COUNT(*) AS count, 'Purchases' AS type
                    FROM purchase_orders GROUP BY order_date
                    UNION ALL
                    SELECT order_date AS period, COUNT(*) AS count, 'Sales' AS type
                    FROM sales_orders GROUP BY order_date
                    ORDER BY period
                    """
                )
                order_chart = cursor.fetchall()

            return jsonify({
                "cards": {
                    "total_products": total_products,
                    "total_materials": total_materials,
                    "low_stock": low_stock,
                    "pending_purchases": pending_purchases,
                    "active_production": active_production,
                    "completed_production": completed_production,
                    "pending_sales": pending_sales,
                    "customers": customers,
                    "suppliers": suppliers,
                },
                "charts": {
                    "inventory": inventory_chart,
                    "production": production_chart,
                    "orders": order_chart,
                },
            })
        finally:
            if connection is not None:
                connection.close()

    @app.get("/")
    def home():
        """Keep the existing static landing page available during migration."""
        return send_from_directory(PROJECT_DIR, "index.html")

    @app.get("/login")
    def login_page():
        return send_from_directory(PROJECT_DIR, "login.html")

    @app.get("/dashboard")
    def dashboard_page():
        return send_from_directory(PROJECT_DIR, "dashboard.html")

    @app.get("/products")
    def products_page():
        return send_from_directory(PROJECT_DIR, "products.html")

    @app.get("/inventory")
    def inventory_page():
        return send_from_directory(PROJECT_DIR, "rawmaterial.html")

    @app.get("/suppliers")
    def suppliers_page():
        return send_from_directory(PROJECT_DIR, "supplier.html")

    @app.get("/purchase")
    def purchase_page():
        return send_from_directory(PROJECT_DIR, "purchase.html")

    @app.get("/production")
    def production_page():
        return send_from_directory(PROJECT_DIR, "production.html")

    @app.get("/customers")
    def customers_page():
        return send_from_directory(PROJECT_DIR, "customers.html")

    @app.get("/sales")
    def sales_page():
        return send_from_directory(PROJECT_DIR, "sales.html")

    @app.get("/audit")
    @login_required
    def audit_page():
        return send_from_directory(PROJECT_DIR, "audit.html")

    @app.get("/notifications")
    @login_required
    def notifications_page():
        return send_from_directory(PROJECT_DIR, "notifications.html")

    @app.get("/reports")
    @login_required
    def reports_page():
        return send_from_directory(PROJECT_DIR, "reports.html")

    @app.get("/bom")
    @login_required
    def bom_page():
        return send_from_directory(PROJECT_DIR, "bom.html")

    @app.get("/download/presentation")
    def download_presentation():
        """Download the generated competition presentation."""
        return send_file(
            PROJECT_DIR / "Manufacturing_ERP_Demo.pptx",
            as_attachment=True,
            download_name="Manufacturing_ERP_Demo.pptx",
            mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    return app


app = create_app()


if __name__ == "__main__":
    # Debug mode is useful while learning; use a production server before deployment.
    app.run(host="127.0.0.1", port=5000, debug=os.getenv("FLASK_DEBUG") == "1")
