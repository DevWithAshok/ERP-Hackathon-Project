# Manufacturing ERP Project Implementation Plan

This document divides the ERP project into practical development steps. The team should complete the steps in order because later modules depend on the database, authentication, and inventory rules created earlier.

The plan is designed to deliver a working 60-70% manufacturing ERP for the competition.

## Overall Development Flow

```text
Project Setup
    -> Database
    -> Backend Foundation
    -> Login and Roles
    -> Master Data
    -> Inventory
    -> Purchase
    -> BOM and Production
    -> Customers and Sales
    -> Dashboard
    -> Reports and Compulsory Features
    -> Testing and Presentation
```

## Step 1: Confirm the Project Scope

### Goal

Agree on exactly what the team will build and avoid spending time on low-priority ERP features.

### Modules included

1. Login and user roles.
2. Dashboard.
3. Products.
4. Raw materials and inventory.
5. Suppliers.
6. Purchases and material receipt.
7. Bill of Materials.
8. Production.
9. Customers.
10. Sales.
11. Reports and compulsory features.

### Main business flow

```text
Supplier
    -> Purchase Order
    -> Material Received
    -> Raw Material Inventory Increases
    -> Production Uses Materials
    -> Finished Product Inventory Increases
    -> Customer Sales Order
    -> Finished Product Inventory Decreases
```

### Do not include initially

- Payroll.
- Accounting.
- Payment gateway.
- Advanced forecasting.
- Multiple warehouses.
- Mobile application.
- Multi-company support.

### Completion check

The complete team agrees on the modules, database tables, user roles, and final demonstration flow.

## Step 2: Divide the Team Responsibilities

### Member 1: Frontend and Integration

- Shared navigation and page layout.
- Login page connection.
- Dashboard cards and charts.
- Responsive design.
- Connecting frontend pages to backend routes.

### Member 2: Products and Inventory

- Product management.
- Raw material management.
- Inventory quantities.
- Low-stock rules and alerts.
- Stock movement history.

### Member 3: Suppliers and Purchases

- Supplier management.
- Purchase orders.
- Material receipt.
- Purchase-to-inventory integration.

### Member 4: BOM and Production

- BOM management.
- Production orders.
- Production status changes.
- Material consumption.
- Finished-product stock update.

### Member 5: Customers, Sales, and Reports

- Customer management.
- Sales orders.
- Stock validation.
- Inventory deduction.
- PDF invoice, Excel export, and QR/barcode.

### Shared coordinator responsibilities

One person must coordinate:

- Database naming.
- Shared fields and status values.
- Git integration.
- Merge conflict resolution.
- End-to-end testing.
- Final demo preparation.

### Completion check

Every team member knows their module and understands how it connects to inventory.

## Step 3: Prepare the Development Environment

### Install

- Python.
- MySQL Server.
- MySQL Workbench or another MySQL client.
- Git.
- VS Code or the team's preferred editor.

### Create the Python environment

```text
python -m venv venv
```

Activate the environment and install the planned packages:

```text
pip install flask flask-sqlalchemy flask-login python-dotenv pymysql
pip install chart.js reportlab openpyxl qrcode pillow
```

The exact package list may be adjusted after choosing the database and PDF approach.

### Create the initial project files

```text
app.py
config.py
requirements.txt
.env.example
schema.sql
seed_data.sql
```

### Important rule

Do not commit real passwords, secret keys, or database credentials. Store them in a local `.env` file.

### Completion check

Python runs successfully, MySQL is available, and the team can start a basic Flask application.

## Step 4: Design and Create the Database

### Required tables

1. `users`
2. `products`
3. `materials`
4. `suppliers`
5. `customers`
6. `inventory`
7. `stock_movements`
8. `purchase_orders`
9. `purchase_order_items`
10. `bom_headers`
11. `bom_items`
12. `production_orders`
13. `sales_orders`
14. `sales_order_items`
15. `notifications`
16. `audit_logs`

### Important relationships

```text
Supplier 1 -> many Purchase Orders
Purchase Order 1 -> many Purchase Items
Material 1 -> one Inventory Record
Product 1 -> one or many BOM Items
Material 1 -> many BOM Items
Product 1 -> many Production Orders
Customer 1 -> many Sales Orders
Product 1 -> many Sales Order Items
User 1 -> many Audit Logs
```

### Important database rules

- Product codes must be unique.
- Material codes must be unique.
- Supplier and customer identifiers must be unique.
- Quantities must not be negative.
- Prices must not be negative.
- Foreign keys must protect related records.
- Deactivate records instead of deleting records that are already used in transactions.

### Prepare demo data

Create these initial records:

- Product: Gear Assembly.
- Materials: Steel, Key, and Bearing.
- Supplier: ABC Metals.
- Customer: XYZ Machines.
- BOM: 5 kg Steel, 2 Keys, and 1 Bearing per Gear Assembly.
- Enough material stock for at least one production order.

### Completion check

The database can be created from `schema.sql`, filled from `seed_data.sql`, and queried without errors.

## Step 5: Create the Flask Backend Foundation

### Build

1. Create the Flask application.
2. Load settings from environment variables.
3. Connect Flask to MySQL.
4. Add a health-check route.
5. Add common error handling.
6. Add templates and static file folders.
7. Add a base layout for shared navigation.

### Recommended structure

```text
app/
|-- __init__.py
|-- auth/
|-- dashboard/
|-- products/
|-- inventory/
|-- suppliers/
|-- purchases/
|-- bom/
|-- production/
|-- customers/
|-- sales/
|-- reports/
|-- services/
|-- templates/
|-- static/
```

### Completion check

The Flask server starts and a health-check page confirms that the backend and database connection are working.

## Step 6: Implement Login and User Roles

### Build

1. Create Administrator, Manager, and Employee users.
2. Hash passwords before storing them.
3. Build the login form.
4. Validate credentials.
5. Create a session after login.
6. Add logout.
7. Add a login-required check.
8. Add a role-required check.
9. Protect backend routes as well as frontend pages.

### Basic permissions

| Role | Main access |
|---|---|
| Administrator | Full system access, users, audit logs, and settings |
| Manager | Dashboard, products, inventory, purchases, production, sales, and reports |
| Employee | Assigned data entry and viewing access |

### Completion check

A valid user can log in, an invalid user is rejected, and each role sees only its permitted actions.

## Step 7: Connect the Existing HTML Screens

### Existing frontend foundation

- `index.html`
- `login.html`
- `dashboard.html`
- `rawmaterial.html`
- `supplier.html`

### Build

1. Move shared navigation into a reusable base template if using Flask templates.
2. Connect the login form to the login route.
3. Connect dashboard cards to live backend data.
4. Connect raw material forms to the database.
5. Connect supplier forms to the database.
6. Display success and error messages.
7. Preserve useful Bootstrap styling while replacing hardcoded values with database values.

### Completion check

A form submission from the browser creates a database record, and refreshing the page loads that record from MySQL.

## Step 8: Build Master Data Modules

Master data is the information used by purchase, production, and sales transactions.

### Modules

- Products.
- Raw materials.
- Suppliers.
- Customers.

### For every module, implement

1. Database table and queries.
2. List page.
3. Add form.
4. Edit form.
5. View details.
6. Deactivate or delete action.
7. Search.
8. Filters.
9. Frontend validation.
10. Backend validation.
11. Role permissions.

### Completion check

Each master record can be added, viewed, edited, searched, filtered, and safely deactivated.

## Step 9: Implement Inventory and Stock Movements

### Build

1. Store raw material quantities.
2. Store finished-product quantities.
3. Create a `stock_movements` table.
4. Create one reusable function for increasing stock.
5. Create one reusable function for decreasing stock.
6. Reject negative quantities.
7. Calculate low-stock status from the minimum stock value.
8. Create a notification when stock becomes low.
9. Record the user, reason, source document, and quantity for every movement.

### Inventory rules

```text
Purchase receipt       -> Raw material stock increases
Production completion  -> Raw material stock decreases
Production completion  -> Finished product stock increases
Sales processing       -> Finished product stock decreases
```

### Completion check

A stock change updates the quantity and creates a matching stock movement record. Negative stock is impossible.

## Step 10: Implement Supplier and Purchase Workflow

### Purchase statuses

```text
Draft -> Ordered -> Received
                    |
                 Cancelled
```

### Build

1. Select a supplier.
2. Add raw materials and quantities.
3. Add prices and calculate the purchase total.
4. Create the purchase order.
5. Add an action to mark it as received.
6. Use a database transaction during receipt.
7. Increase raw material inventory only on receipt.
8. Prevent the same order from being received twice.
9. Create a notification and audit record.

### Example test

```text
Before receipt: Steel = 100 kg
Received: 50 kg
After receipt: Steel = 150 kg
```

### Completion check

A purchase order can be created and received, and the raw material quantity increases exactly once.

## Step 11: Implement BOM Management

### Build

1. Select a finished product.
2. Add the raw materials used by that product.
3. Enter quantity required per product unit.
4. Validate that quantities are greater than zero.
5. Prevent duplicate material lines in the same BOM.
6. Allow the BOM to be viewed and edited.

### Example BOM

| Product | Material | Quantity per unit |
|---|---|---:|
| Gear Assembly | Steel | 5 kg |
| Gear Assembly | Key | 2 Nos |
| Gear Assembly | Bearing | 1 No |

### Completion check

The system can calculate the exact raw materials required for any requested production quantity.

## Step 12: Implement Production Workflow

### Production statuses

```text
Pending -> In Progress -> Completed
     |          |
 Cancelled   Cancelled
```

### Build

1. Select a product.
2. Enter the production quantity.
3. Load the product BOM.
4. Multiply BOM quantities by the production quantity.
5. Check raw material stock.
6. Reject production when stock is insufficient.
7. Start production.
8. Complete production inside a database transaction.
9. Deduct raw materials.
10. Increase finished-product inventory.
11. Record stock movements and audit history.
12. Prevent completion twice.

### Example test

For 10 Gear Assemblies:

```text
Steel required: 50 kg
Keys required: 20 Nos
Bearings required: 10 Nos
Finished stock increase: 10 Gear Assemblies
```

### Completion check

Production completion updates raw material and finished-product stock correctly in one transaction.

## Step 13: Implement Customers and Sales Workflow

### Build

1. Create customer management.
2. Select a customer and finished product.
3. Enter the requested quantity.
4. Load the current unit price.
5. Calculate the order total.
6. Check available finished-product stock.
7. Reject a sale that exceeds stock.
8. Process the sale inside a database transaction.
9. Decrease finished-product inventory exactly once.
10. Record an audit entry and notification.

### Sales statuses

```text
Pending -> Confirmed -> Processed
                 |
              Cancelled
```

### Completion check

A successful sale reduces finished-product stock, while an excessive sale is rejected without changing the database.

## Step 14: Implement the Dashboard

### Summary cards

The dashboard must load these values from MySQL:

- Total products.
- Total raw materials.
- Low-stock items.
- Pending purchases.
- Active production orders.
- Completed production orders.
- Pending sales orders.
- Total customers.
- Total suppliers.

### Required charts

1. Inventory available versus low stock.
2. Purchases and sales over time.
3. Production status distribution.

### Completion check

Creating, receiving, completing, or processing a transaction changes the dashboard after refresh.

## Step 15: Add Compulsory Competition Features

Add these features after the three core workflows work:

### Required features

1. PDF invoice.
2. Excel export.
3. QR code or barcode.
4. Automatic low-stock alert.
5. Three or more charts.
6. Responsive interface.
7. Notifications.
8. Audit log.
9. Frontend and backend validation.
10. Search and filters.

### Recommended order

1. Validation.
2. Search and filters.
3. Low-stock notifications.
4. Audit log.
5. PDF invoice.
6. Excel export.
7. QR code or barcode.
8. Responsive layout review.

### Completion check

Every required feature works with real database records and can be shown during the final demonstration.

## Step 16: Add Security and Error Handling

### Verify

- Protected pages redirect unauthenticated users.
- Backend routes enforce role permissions.
- Passwords are hashed.
- Database credentials are not committed.
- SQL queries use parameters or an ORM.
- Invalid IDs return clear errors.
- Empty and invalid form values are rejected.
- Duplicate receipt and completion actions are rejected.
- User input is safely rendered.
- Database transactions roll back when an operation fails.

### Completion check

Invalid actions do not corrupt inventory, orders, or user data.

## Step 17: Test Each Module

### Authentication tests

- [ ] Valid login succeeds.
- [ ] Invalid login fails.
- [ ] Logout works.
- [ ] Role restrictions work.

### Master data tests

- [ ] Add works.
- [ ] View works.
- [ ] Edit works.
- [ ] Deactivate or delete works.
- [ ] Search works.
- [ ] Filters work.
- [ ] Invalid input is rejected.

### Integration tests

- [ ] Purchase receipt increases raw material stock.
- [ ] Duplicate receipt is rejected.
- [ ] Production consumes raw materials.
- [ ] Production increases finished-product stock.
- [ ] Insufficient raw material blocks production.
- [ ] Sale reduces finished-product stock.
- [ ] Insufficient finished stock blocks sale.
- [ ] No stock becomes negative.

### Compulsory feature tests

- [ ] PDF invoice has correct values.
- [ ] Excel export contains current records.
- [ ] QR code or barcode contains a useful order reference.
- [ ] Low-stock notification appears.
- [ ] Audit log records important actions.
- [ ] Charts display live values.
- [ ] Layout works on desktop and mobile widths.

## Step 18: Run the Complete Demonstration Test

Use one prepared scenario so the presentation is reliable.

```text
Supplier: ABC Metals
Materials: Steel, Key, Bearing
Product: Gear Assembly
BOM: 5 kg Steel + 2 Keys + 1 Bearing per unit
Customer: XYZ Machines
```

### Demo order

1. Log in as Manager.
2. Open the dashboard.
3. Show current inventory.
4. Create a purchase order for steel.
5. Mark the order as received.
6. Show that steel stock increased.
7. Open the Gear Assembly BOM.
8. Create a production order.
9. Complete production.
10. Show raw materials decreased.
11. Show finished-product stock increased.
12. Select the customer.
13. Create a sales order.
14. Show stock validation.
15. Process the sale.
16. Show finished-product stock decreased.
17. Generate the PDF invoice.
18. Show the charts, notification, export, QR/barcode, and audit log.

### Completion check

The entire flow works from a clean demo database without manually changing database values between steps.

## Step 19: Prepare the Presentation

Explain the application in this order:

1. The manufacturing company's spreadsheet problem.
2. What ERP means.
3. How this ERP connects departments.
4. The application architecture.
5. The database relationships.
6. Purchase and inventory integration.
7. BOM and production integration.
8. Customer and sales integration.
9. Role-based access.
10. Compulsory features.
11. Future improvements.

Every team member must be able to explain:

- Their own module.
- The related database tables.
- The validation rules.
- How their module updates inventory or connects to another module.

## Step 20: Final Definition of Done

The project is ready when all of these statements are true:

- The application starts locally.
- MySQL stores the real application data.
- Login and role restrictions work.
- Products, materials, suppliers, and customers support CRUD operations.
- Purchase receipt increases raw material inventory.
- BOM-driven production consumes raw materials.
- Production creates finished-product inventory.
- Sales validate stock and reduce finished-product inventory.
- Negative inventory is prevented.
- Dashboard values are live.
- At least three charts work.
- Low-stock notifications work.
- Audit logs work.
- PDF invoice works.
- Excel export works.
- QR code or barcode works.
- Search, filters, and validation work.
- The responsive interface works.
- The complete demonstration succeeds without direct database edits.
- The team can explain the project confidently.

## Priority When Time Is Limited

```text
1. Database and login
2. Inventory rules
3. Purchase -> receipt -> inventory
4. BOM -> production -> inventory
5. Customer -> sale -> inventory
6. Dashboard and charts
7. Validation, search, notifications, and audit log
8. PDF, Excel, and QR/barcode
9. Visual polish
10. Optional future modules
```

The project should always prefer a smaller working ERP flow over many unfinished screens.
