# Manufacturing ERP Implementation Specification

## 1. Document Purpose

This document describes the current project state, the required ERP functionality, missing components, implementation order, and acceptance criteria for the MWS TECHSPRINT 2026 project.

The target is not a complete commercial ERP. The target is a reliable demonstration of approximately **60-70% of a manufacturing ERP**, focused on the workflows that prove real integration:

```text
Purchase -> Material Receipt -> Raw Material Inventory Increase
BOM -> Production Completion -> Raw Material Deduction + Finished Stock Increase
Customer Sale -> Stock Check -> Sales Processing -> Finished Stock Reduction
```

The project should be judged as a working connected system, not only as a collection of HTML screens.

## 2. Current Project Status

### 2.1 What currently exists

The workspace currently contains these frontend files:

| File | Current purpose |
|---|---|
| `index.html` | Existing main or landing page foundation |
| `login.html` | Login page foundation |
| `dashboard.html` | Dashboard page foundation |
| `rawmaterial.html` | Raw material and inventory page foundation |
| `supplier.html` | Supplier page foundation |
| `README.md` | Project explanation, scope, modules, workflows, and competition checklist |

These files provide a starting point for the user interface.

### 2.2 What is not implemented yet

Based on the current workspace, the following major parts still need to be added:

- Flask backend application.
- MySQL database and schema.
- Database connection and configuration.
- Real login authentication.
- Password hashing and session handling.
- Role-based access control.
- CRUD APIs and database queries.
- Product page and product APIs.
- Customer page and customer APIs.
- Purchase order page and purchase APIs.
- Purchase receipt logic.
- BOM page and BOM APIs.
- Production page and production APIs.
- Sales page and sales APIs.
- Inventory transaction logic.
- Dashboard APIs and live statistics.
- PDF invoice generation.
- Excel export.
- QR code or barcode generation.
- Notifications.
- Audit log.
- Server-side validation.
- Search and filtering connected to the database.
- Automated tests and end-to-end workflow testing.

The existing HTML files must therefore be treated as UI groundwork, not as completed ERP functionality.

## 3. Project Goal

Build one connected web application for a manufacturing company that currently manages information in separate spreadsheets.

The application must provide one reliable source of information for:

- Users and roles.
- Products.
- Raw materials.
- Inventory.
- Suppliers.
- Purchase orders.
- Bill of Materials.
- Production orders.
- Customers.
- Sales orders.
- Reports and operational history.

## 4. Technology Specification

Use the following stack unless the team has a strong reason to change it:

| Area | Technology |
|---|---|
| Frontend | HTML, CSS, Bootstrap, JavaScript |
| Backend | Python, Flask |
| Database | MySQL |
| Database access | SQLAlchemy or a well-structured MySQL connector |
| Charts | Chart.js |
| PDF | ReportLab or WeasyPrint |
| Excel | openpyxl or pandas |
| QR code | qrcode |
| Authentication | Flask sessions with hashed passwords |
| Version control | Git |

Keep the existing HTML approach. React is not necessary for this competition if the team can deliver more reliable functionality with Flask templates and JavaScript.

## 5. Target System Architecture

```text
User Browser
    |
    | HTML + Bootstrap + JavaScript
    v
Flask Routes and APIs
    |
    | Authentication, validation, business rules
    v
Service or Business Logic Layer
    |
    | Database transactions
    v
MySQL Database
```

### 5.1 Recommended project structure

The current flat HTML files can gradually be reorganized into this structure:

```text
erp-project/
|
|-- app.py
|-- config.py
|-- requirements.txt
|-- .env.example
|-- schema.sql
|-- seed_data.sql
|
|-- app/
|   |-- __init__.py
|   |-- auth/
|   |-- dashboard/
|   |-- products/
|   |-- inventory/
|   |-- suppliers/
|   |-- purchases/
|   |-- bom/
|   |-- production/
|   |-- customers/
|   |-- sales/
|   |-- reports/
|   |-- services/
|   |-- templates/
|   |-- static/
|       |-- css/
|       |-- js/
|       |-- images/
|
|-- tests/
|   |-- test_auth.py
|   |-- test_inventory.py
|   |-- test_workflows.py
```

A simple single-file Flask backend can be used initially, but separating business logic into modules will make integration easier for a five-member team.

## 6. Functional Requirements

### 6.1 Authentication and roles

The system must support:

- Administrator.
- Manager.
- Employee.

Required behavior:

- Users can log in with valid credentials.
- Invalid credentials are rejected.
- Passwords are stored as hashes, never as plain text.
- A user session is created after successful login.
- Logout destroys the session.
- Each backend route checks the user's permission.
- The interface hides actions that a role cannot use.

Suggested permissions:

| Module | Administrator | Manager | Employee |
|---|---|---|---|
| Users and roles | Full | View | No access |
| Products | Full | Add/edit/view | View |
| Inventory | Full | Add/edit/view | View/update assigned records |
| Suppliers | Full | Full | View |
| Purchases | Full | Full | Create/view |
| BOM | Full | Full | View |
| Production | Full | Full | Update status |
| Customers | Full | Full | Add/edit/view |
| Sales | Full | Full | Create/view |
| Reports and audit log | Full | View | Limited view |

### 6.2 Products

Required fields:

- Product code.
- Product name.
- Category.
- Selling price.
- Description.
- Active status.

Required actions:

- Add.
- View.
- Edit.
- Deactivate or delete.
- Search.
- Filter by category and status.

### 6.3 Raw materials and inventory

Required fields:

- Material code.
- Material name.
- Category.
- Unit.
- Quantity.
- Minimum stock.
- Supplier.
- Status.

Required rules:

- Status is `Available` when quantity is above the minimum stock.
- Status is `Low Stock` when quantity is less than or equal to the minimum stock.
- Quantity cannot be negative.
- Every stock change records the reason and user.
- Search and filtering are available.

### 6.4 Suppliers

Required fields:

- Supplier code.
- Supplier name.
- Phone.
- Email.
- Address.
- Materials supplied.
- Active status.

Required actions are add, view, edit, deactivate, search, and filter.

### 6.5 Purchases and receipts

Required purchase states:

```text
Draft -> Ordered -> Received
                    |
                 Cancelled
```

Required behavior:

1. Select a supplier.
2. Add one or more materials.
3. Enter ordered quantities and unit prices.
4. Save the purchase order.
5. Mark the order as received.
6. Increase inventory only once when the receipt is confirmed.
7. Prevent duplicate receipt processing.
8. Write an audit entry and notification.

### 6.6 Bill of Materials

A BOM connects one finished product to its required raw materials.

Required data:

- Product.
- Material.
- Quantity required per product unit.
- Unit.
- Active status.

Required rules:

- A product can have multiple BOM items.
- A material can be used in many BOMs.
- Duplicate material lines in one BOM should be rejected or combined.
- BOM quantities must be greater than zero.

### 6.7 Production

Required production states:

```text
Pending -> In Progress -> Completed
     |          |
 Cancelled   Cancelled
```

Required behavior:

1. Select a product and production quantity.
2. Load its BOM.
3. Calculate material requirements.
4. Check raw material availability.
5. Start production.
6. On completion, deduct the required materials.
7. Increase finished-product inventory.
8. Prevent completion when stock is insufficient.
9. Prevent the same order from being completed twice.
10. Record the action in the audit log.

### 6.8 Customers and sales

Customer fields:

- Customer code.
- Customer name.
- Phone.
- Email.
- Address.
- Active status.

Sales order fields:

- Sales order number.
- Customer.
- Product.
- Quantity.
- Unit price.
- Total.
- Status.
- Order date.

Required behavior:

1. Select a customer and product.
2. Enter the quantity.
3. Calculate the total on the frontend and backend.
4. Check finished-product stock.
5. Reject the request if stock is insufficient.
6. Process the sale.
7. Reduce inventory once.
8. Generate a PDF invoice.
9. Record an audit entry and notification.

## 7. Database Specification

### 7.1 Required tables

At minimum, create these tables:

- `users`
- `products`
- `materials`
- `suppliers`
- `customers`
- `inventory`
- `purchase_orders`
- `purchase_order_items`
- `bom_headers`
- `bom_items`
- `production_orders`
- `sales_orders`
- `sales_order_items`
- `notifications`
- `audit_logs`
- `stock_movements`

### 7.2 Important keys and relationships

- `inventory.material_id` references `materials.id`.
- `inventory.product_id` references `products.id` for finished goods, or use a separate inventory type.
- `purchase_orders.supplier_id` references `suppliers.id`.
- `purchase_order_items.purchase_order_id` references `purchase_orders.id`.
- `purchase_order_items.material_id` references `materials.id`.
- `bom_headers.product_id` references `products.id`.
- `bom_items.bom_id` references `bom_headers.id`.
- `bom_items.material_id` references `materials.id`.
- `production_orders.product_id` references `products.id`.
- `sales_orders.customer_id` references `customers.id`.
- `sales_order_items.sales_order_id` references `sales_orders.id`.
- `sales_order_items.product_id` references `products.id`.
- `audit_logs.user_id` references `users.id`.

Use primary keys, foreign keys, unique constraints, non-negative quantity checks, and indexes for searchable fields.

### 7.3 Transaction requirements

These operations must run inside database transactions:

- Material receipt.
- Production completion.
- Sales processing.

Example production transaction:

```text
Begin transaction
  Check production status
  Check all required material quantities
  Deduct raw materials
  Add finished product quantity
  Mark production as Completed
  Insert stock movements
  Insert audit log
Commit transaction
```

If any step fails, roll back every change.

## 8. API and Page Requirements

Suggested API groups:

```text
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/dashboard/summary
GET    /api/products
POST   /api/products
PUT    /api/products/<id>
DELETE /api/products/<id>
GET    /api/materials
POST   /api/materials
GET    /api/inventory
GET    /api/suppliers
POST   /api/suppliers
GET    /api/purchases
POST   /api/purchases
POST   /api/purchases/<id>/receive
GET    /api/boms
POST   /api/boms
GET    /api/production
POST   /api/production
POST   /api/production/<id>/start
POST   /api/production/<id>/complete
GET    /api/customers
POST   /api/customers
GET    /api/sales
POST   /api/sales
POST   /api/sales/<id>/process
GET    /api/audit-logs
GET    /api/exports/inventory.xlsx
GET    /api/sales/<id>/invoice.pdf
```

The exact URL design may change, but routes should use consistent HTTP methods, return useful status codes, validate input, and return clear error messages.

## 9. Features That Must Be Added

### High priority: required for the core demonstration

- [ ] Flask application starts successfully.
- [ ] MySQL schema is created.
- [ ] Seed data exists for the demo.
- [ ] Login works.
- [ ] Role restrictions work on the backend.
- [ ] Products can be managed.
- [ ] Materials and inventory can be managed.
- [ ] Suppliers can be managed.
- [ ] Purchases can be created and received.
- [ ] Receiving updates raw material inventory.
- [ ] BOMs can be created and viewed.
- [ ] Production orders can be started and completed.
- [ ] Production updates raw and finished-product inventory.
- [ ] Customers can be managed.
- [ ] Sales orders check stock and update inventory.
- [ ] Dashboard values come from MySQL.

### Medium priority: compulsory competition features

- [ ] Three charts.
- [ ] Automatic low-stock alert.
- [ ] Notifications.
- [ ] Audit log.
- [ ] Search and filters.
- [ ] Frontend and backend form validation.
- [ ] Responsive layout.
- [ ] PDF invoice.
- [ ] Excel export.
- [ ] QR code or barcode.

### Lower priority: future improvements

- [ ] Payroll.
- [ ] Accounting.
- [ ] Multiple warehouses.
- [ ] Payments.
- [ ] Forecasting.
- [ ] Mobile app.
- [ ] Multi-company support.

Do not delay the three integrated workflows for lower-priority features.

## 10. Step-by-Step Implementation Guide

### Step 1: Confirm the scope

Freeze the competition scope around these modules:

1. Login and roles.
2. Dashboard.
3. Products.
4. Raw materials and inventory.
5. Suppliers.
6. Purchases.
7. BOM.
8. Production.
9. Customers.
10. Sales.
11. Reports and compulsory features.

Do not begin with payroll, accounting, or advanced features.

**Completion check:** The team agrees on the same tables, workflows, names, and demo scenario.

### Step 2: Install and verify the environment

Install and verify:

- Python.
- MySQL Server.
- MySQL Workbench or another database client.
- A code editor.
- Git.

Create a virtual environment and install the backend dependencies from `requirements.txt`.

**Completion check:** Python can start Flask and the application can connect to MySQL.

### Step 3: Create the database

1. Create a database named for the ERP project.
2. Create the tables and relationships.
3. Add foreign keys and constraints.
4. Add indexes for code, name, status, and dates.
5. Add seed data for users, products, materials, suppliers, customers, BOMs, and inventory.

Prepare a small demo dataset:

- One Gear Assembly product.
- Steel, Key, and Bearing materials.
- One supplier.
- One customer.
- A Gear Assembly BOM.
- Enough raw materials for production.

**Completion check:** The team can query every table and explain each relationship.

### Step 4: Create the Flask foundation

1. Create the Flask application.
2. Add configuration through environment variables.
3. Add the MySQL connection.
4. Add a health-check route.
5. Add common error handling.
6. Add JSON response helpers if using APIs.
7. Add a base template and static file folders.

Never commit real database passwords. Use a local `.env` file and keep `.env` out of Git.

**Completion check:** Opening the health-check URL returns a successful response.

### Step 5: Implement authentication first

1. Create the user table and seed three roles.
2. Hash passwords.
3. Implement login.
4. Implement logout.
5. Store the logged-in user in a session.
6. Add a reusable login-required check.
7. Add a reusable role-required check.
8. Protect both pages and backend routes.

**Completion check:** Administrator, Manager, and Employee accounts show different permitted actions.

### Step 6: Connect the existing frontend foundation

1. Preserve useful Bootstrap layout and styling from the existing HTML files.
2. Move shared navigation into a base template or shared component.
3. Connect login form submission to Flask.
4. Connect dashboard cards to a dashboard endpoint.
5. Connect raw material and supplier forms to backend routes.
6. Display success and error notifications.

**Completion check:** A record submitted from the browser appears in MySQL and can be loaded again.

### Step 7: Build master data modules

Implement these modules before transaction modules:

- Products.
- Materials.
- Suppliers.
- Customers.

For each module, implement:

1. Database model or queries.
2. List route.
3. Add route.
4. Edit route.
5. Deactivate or delete route.
6. Search and filter.
7. Frontend form.
8. Validation.
9. Permission checks.

**Completion check:** Each record can be added, viewed, edited, searched, and safely deactivated.

### Step 8: Implement inventory and stock movements

1. Create inventory records for raw materials and finished products.
2. Create a stock movement table.
3. Write one service for increasing stock.
4. Write one service for decreasing stock.
5. Reject negative quantities.
6. Calculate low-stock status.
7. Create notifications for low-stock items.
8. Ensure every stock update records its source document and user.

**Completion check:** A manual test stock increase and decrease produces the correct quantity and movement history.

### Step 9: Implement purchase and receipt workflow

1. Create purchase order tables.
2. Create purchase order list and form.
3. Select a supplier and materials.
4. Save the order as Ordered.
5. Add a Receive action.
6. Use a transaction to update inventory.
7. Prevent receiving an already received order.
8. Add an audit log and notification.

**Completion check:** Receiving 100 kg of steel changes the database quantity from the old value to old value plus 100 kg exactly once.

### Step 10: Implement BOM and production workflow

1. Create BOM header and item screens.
2. Allow a product to have multiple raw material requirements.
3. Create production orders.
4. Calculate material requirements from the BOM.
5. Check all required material stock before starting or completing.
6. Implement Pending, In Progress, and Completed states.
7. Use a transaction on completion.
8. Deduct raw materials.
9. Add finished products.
10. Record stock movements and audit history.

**Completion check:** Completing 10 Gear Assemblies consumes exactly the BOM quantities multiplied by 10 and adds 10 finished products.

### Step 11: Implement customers and sales workflow

1. Create customer management.
2. Create sales order form and list.
3. Calculate totals from quantity and unit price.
4. Check finished-product stock.
5. Reject insufficient stock.
6. Process the sale inside a transaction.
7. Deduct finished-product inventory exactly once.
8. Add the audit entry.

**Completion check:** A sale cannot create negative stock and a successful processed sale reduces inventory by the sold quantity.

### Step 12: Implement the dashboard

Create a dashboard service that returns live database values for:

- Product count.
- Material count.
- Low-stock count.
- Pending purchase count.
- Active production count.
- Completed production count.
- Pending sales count.
- Customer count.
- Supplier count.

Add at least three charts:

1. Inventory available versus low stock.
2. Purchase and sales activity over time.
3. Production status distribution.

**Completion check:** Creating or processing a transaction changes the dashboard after refresh.

### Step 13: Add compulsory features

Implement in this order:

1. Server-side validation.
2. Search and filters.
3. Low-stock notifications.
4. Audit log.
5. PDF invoice.
6. Excel export.
7. QR code or barcode.
8. Responsive layout review.

For each feature, connect it to real records rather than sample-only values.

**Completion check:** Every compulsory feature can be demonstrated from the application during the final presentation.

### Step 14: Add error handling and security checks

Verify that:

- Unauthenticated users cannot access protected routes.
- Employees cannot call manager-only endpoints manually.
- Invalid IDs return a useful error.
- Invalid quantities are rejected.
- Duplicate receipt and completion actions are rejected.
- SQL queries use parameters or an ORM.
- Passwords are hashed.
- Secrets are stored outside source control.
- User input is escaped in rendered HTML.

**Completion check:** Attempting invalid actions does not corrupt the database.

### Step 15: Prepare realistic demo data

Prepare one complete scenario before the presentation:

```text
Supplier: ABC Metals
Materials: Steel, Key, Bearing
Product: Gear Assembly
BOM: 5 kg Steel + 2 Keys + 1 Bearing per unit
Customer: XYZ Machines
```

Use this scenario to show purchase, receipt, production, and sale without entering unnecessary data live.

### Step 16: Test the complete workflow

Run this exact sequence:

1. Log in as Manager.
2. Review the dashboard.
3. Create or select a supplier.
4. Create a purchase order.
5. Receive materials.
6. Confirm raw material inventory increased.
7. Open the BOM.
8. Create and complete production.
9. Confirm raw material inventory decreased.
10. Confirm finished-product inventory increased.
11. Create a customer sale.
12. Confirm stock validation.
13. Process the sale.
14. Confirm finished-product inventory decreased.
15. Generate the invoice.
16. Show the charts, notification, export, QR/barcode, and audit log.

**Completion check:** The entire flow works from a clean database without manual database edits between steps.

### Step 17: Prepare the presentation

Explain the project in this order:

1. The spreadsheet problem.
2. What ERP means and why it helps.
3. The application architecture.
4. The database relationships.
5. The purchase workflow.
6. The production and BOM workflow.
7. The sales workflow.
8. The compulsory features.
9. Role-based access.
10. Future improvements outside the current scope.

Each team member should understand their own module and the shared inventory rules.

## 11. Acceptance Criteria

The 60-70% target is considered achieved when all of the following are true:

- The application starts locally.
- MySQL stores the application data.
- Login and role restrictions work.
- Products, materials, suppliers, and customers have working CRUD operations.
- Purchase receipt increases raw material inventory.
- BOM-driven production consumes raw materials and creates finished stock.
- Sales validate stock and reduce finished stock.
- No workflow can create negative stock.
- Dashboard values are based on database data.
- At least three charts work.
- Low-stock notifications work.
- Audit logs record important actions.
- PDF invoice and Excel export work.
- QR code or barcode works.
- Search, filters, validation, and responsive layout work.
- The full demo flow passes without direct database manipulation.

## 12. Priority When Time Is Limited

Use this priority order:

```text
1. Database and login
2. Inventory rules
3. Purchase -> receipt -> inventory
4. BOM -> production -> inventory
5. Customer -> sale -> inventory
6. Dashboard and charts
7. Validation, search, notifications, audit log
8. PDF, Excel, QR/barcode
9. Visual polish
10. Optional future modules
```

A smaller working workflow is more valuable than many unfinished pages.

## 13. Definition of Success

The project succeeds when a judge can see that:

- The application solves the company's separate-spreadsheet problem.
- Different ERP modules use the same database.
- Purchase, production, inventory, and sales are connected.
- Business rules are enforced by the backend.
- The dashboard reflects actual transactions.
- The team can explain how the system works.
- The required extra features are visible and usable.

The final product should be presented as a focused, working manufacturing ERP demonstration rather than as a claim to have built every feature of a commercial ERP.
