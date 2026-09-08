# Manufacturing ERP System

A web-based Enterprise Resource Planning (ERP) system for a manufacturing company. The project brings products, raw materials, suppliers, purchasing, production, customers, sales, inventory, and reports into one connected application.

This project is being prepared for the MWS TECHSPRINT 2026 ERP development competition. The goal is to demonstrate approximately 60-70% of a complete manufacturing ERP with working business workflows, database integration, and compulsory features.

## 1. What Is ERP?

ERP means **Enterprise Resource Planning**.

An ERP system connects the important activities of an organization in one application. Instead of maintaining separate spreadsheets for products, suppliers, stock, purchases, production, customers, and sales, all departments use shared data from one system.

### Why ERP Is Useful

An ERP helps a manufacturing company to:

- Store business data in one central database.
- Avoid duplicate and inconsistent spreadsheet data.
- Track raw material and finished-product stock.
- Connect suppliers with purchases and inventory.
- Connect production with the Bill of Materials (BOM).
- Check stock before accepting sales orders.
- Reduce manual calculations and data-entry errors.
- Give managers a real-time overview through dashboards.
- Maintain user roles, notifications, and an audit history.
- Produce reports and documents for business decisions.

## 2. Project Objective

Build a connected manufacturing ERP that supports this main chain:

```text
Supplier
   |
Purchase Order
   |
Material Received
   |
Raw Material Inventory Increases
   |
Production Uses Raw Materials
   |
Finished Product Inventory Increases
   |
Customer Sales Order
   |
Finished Product Inventory Decreases
```

The most important objective is not to create many disconnected pages. The objective is to make the modules share data and update inventory through real business actions.

## 3. Target Scope: 60-70% ERP Demonstration

A complete commercial ERP is very large. For the competition, this project will focus on the most valuable and demonstrable functionality.

### Core functionality to complete

- Login with Administrator, Manager, and Employee roles.
- Dashboard with live summary cards.
- Product management.
- Raw material and inventory management.
- Supplier management.
- Purchase order creation and material receipt.
- Automatic raw material stock increase after receipt.
- Bill of Materials (BOM) management.
- Production order creation and status tracking.
- Automatic finished-product stock increase after production completion.
- Customer management.
- Sales order creation with stock checking.
- Automatic finished-product stock reduction after sale processing.
- Search and filter on important lists.
- Form validation and stock alerts.
- Audit log for important actions.
- At least three dashboard charts.
- PDF invoice generation.
- Excel export.
- QR code or barcode generation.
- Responsive Bootstrap-based interface.

### Features that can remain outside the first competition version

These are useful in a full ERP but are lower priority for the 60-70% target:

- Payroll and human resources.
- Accounting and tax filing.
- Multi-warehouse transfers.
- Advanced demand forecasting.
- Supplier payment processing.
- Customer payment gateway integration.
- Complex approval hierarchies.
- Mobile application.
- Multi-company and multi-currency support.

## 4. Planned Technology Stack

The recommended stack is based on the team's existing HTML, CSS, Bootstrap, JavaScript, and Python knowledge.

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, Bootstrap, JavaScript |
| Backend | Python and Flask |
| Database | MySQL |
| Charts | Chart.js |
| PDF | Python PDF library such as ReportLab or WeasyPrint |
| Excel | Python library such as openpyxl or pandas |
| QR code | Python `qrcode` library |
| API style | Flask routes returning HTML or JSON |

The current workspace contains initial HTML screens such as the login, dashboard, raw material, and supplier pages. These screens are the frontend foundation. The next major step is connecting them to Flask APIs and MySQL instead of using hardcoded data.

## 5. Main Modules

### 5.1 Login and Role Management

Required roles:

- **Administrator**: full access, user management, configuration, audit log, and all modules.
- **Manager**: dashboard, suppliers, purchases, production, sales, and reports.
- **Employee**: day-to-day data entry and viewing access for assigned modules.

The login system should validate credentials and restrict actions according to the logged-in user's role.

### 5.2 Products

Store and manage finished products.

Required fields:

- Product ID or code.
- Product name.
- Category.
- Selling price.
- Description.
- Current stock.
- Status.

Required actions:

- Add product.
- View products.
- Edit product.
- Delete or deactivate product.
- Search and filter products.

### 5.3 Raw Materials and Inventory

Store the materials used to manufacture products and track their quantities.

Example fields:

| Field | Example |
|---|---|
| Material ID | RM-001 |
| Material name | Steel |
| Category | Metal |
| Quantity | 250 |
| Minimum stock | 50 |
| Unit | kg |
| Supplier | ABC Metals |
| Status | Available or Low Stock |

The system must automatically show **Low Stock** when the quantity is less than or equal to the minimum stock level.

### 5.4 Suppliers

Store supplier contact and supply information.

Required fields:

- Supplier ID.
- Supplier name.
- Phone.
- Email.
- Address.
- Material supplied.

Required actions:

- Add supplier.
- View suppliers.
- Edit supplier.
- Delete or deactivate supplier.
- Search and filter suppliers.

### 5.5 Purchase and Material Receipt

Purchase is connected to suppliers and raw material inventory.

Required workflow:

1. Select a supplier.
2. Create a purchase order.
3. Add one or more raw materials and quantities.
4. Save the order as Pending or Ordered.
5. Receive the material.
6. Update the purchase status to Received.
7. Increase inventory by the received quantity.
8. Add the action to the audit log and notifications.

Example:

```text
Existing Steel stock: 100 kg
Received from purchase order: 50 kg
New Steel stock: 150 kg
```

Inventory must increase only when the material is marked as received, not merely when the purchase order is created.

### 5.6 Bill of Materials (BOM)

A BOM defines the raw materials required to manufacture one unit of a product.

Example: Gear Assembly

| Raw material | Required quantity |
|---|---:|
| Steel | 5 kg |
| Key | 2 Nos |
| Bearing | 1 No |

The BOM allows the system to calculate the materials needed for a production quantity.

For 10 Gear Assemblies:

- Steel required: 50 kg.
- Key required: 20 Nos.
- Bearing required: 10 Nos.

### 5.7 Production

Production converts raw materials into finished products.

Required statuses:

```text
Pending -> In Progress -> Completed
```

Required workflow:

1. Select a product.
2. Enter the production quantity.
3. Read the product's BOM.
4. Calculate the required raw materials.
5. Check whether raw material stock is sufficient.
6. Start production.
7. On completion, deduct the used raw materials.
8. Increase finished-product inventory.
9. Add the action to the audit log.

Example:

```text
Production quantity: 10 Gear Assemblies
Steel consumed: 50 kg
Finished product stock increase: 10 Gear Assemblies
```

### 5.8 Customers and Sales

Store customer details and process sales orders.

Customer fields:

- Customer ID.
- Customer name.
- Phone.
- Email.
- Address.

Sales order fields:

- Sales order ID.
- Customer.
- Product.
- Quantity.
- Unit price.
- Total amount.
- Status.
- Order date.

Required workflow:

1. Select a customer.
2. Select a product.
3. Enter the quantity.
4. Check available finished-product stock.
5. Calculate the total automatically.
6. Create the sales order.
7. On processing or confirmation, reduce inventory.
8. Generate a PDF invoice.
9. Add the sale to the audit log.

The application must reject a sale when the requested quantity is greater than available stock.

### 5.9 Dashboard

The dashboard is the main management screen. It should read data from the database and display live values for:

- Total products.
- Total raw materials.
- Low-stock materials.
- Pending purchases.
- Active production orders.
- Completed production orders.
- Pending sales orders.
- Total customers.
- Total suppliers.

At least three charts should be included:

1. **Inventory status chart**: available stock versus low stock.
2. **Purchase and sales chart**: orders over time.
3. **Production status chart**: pending, in-progress, and completed production.

## 6. Database Design

The application must use MySQL. Data should not be permanently hardcoded in the frontend.

### Main tables

- `users`
- `roles` or a role field in `users`
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

### Important relationships

```text
Supplier 1 ---- many Purchase Orders
Purchase Order 1 ---- many Purchase Order Items
Material 1 ---- 1 Inventory Record
Product 1 ---- 1 BOM Header
BOM Header 1 ---- many BOM Items
Material 1 ---- many BOM Items
Product 1 ---- many Production Orders
Customer 1 ---- many Sales Orders
Sales Order 1 ---- many Sales Order Items
Product 1 ---- many Sales Order Items
```

### Inventory rules

- Receiving a purchase increases raw material inventory.
- Completing production decreases raw material inventory.
- Completing production increases finished-product inventory.
- Processing a sale decreases finished-product inventory.
- Inventory quantity must never become negative.
- Low-stock status is calculated using the minimum stock value.

Database transactions should be used for purchase receipt, production completion, and sales processing so that all related updates succeed or fail together.

## 7. Backend and Frontend Architecture

```text
Browser UI
   |
HTML + Bootstrap + JavaScript
   |
Flask Routes / API Endpoints
   |
Business Logic and Validation
   |
MySQL Database
```

Suggested backend areas:

- Authentication and role checking.
- Product routes.
- Material and inventory routes.
- Supplier routes.
- Purchase routes.
- BOM routes.
- Production routes.
- Customer and sales routes.
- Dashboard summary routes.
- Report, PDF, Excel, and QR routes.

Every form should validate required fields on the frontend and backend. Backend validation is essential because frontend validation alone can be bypassed.

## 8. Compulsory Features Checklist

- [ ] PDF invoice.
- [ ] Excel export.
- [ ] QR code or barcode.
- [ ] Automatic low-stock alert.
- [ ] Three or more charts.
- [ ] Responsive UI.
- [ ] Notifications.
- [ ] Audit log.
- [ ] Form validation.
- [ ] Search and filter.
- [ ] Role-based access.
- [ ] Database-backed records.

## 9. Suggested Team Responsibilities

### Member 1: Frontend and Integration

- Login screen.
- Navigation and common layout.
- Dashboard cards and charts.
- Responsive design.
- Integration of pages with backend APIs.

### Member 2: Products and Inventory

- Product CRUD.
- Raw material CRUD.
- Inventory quantity and status.
- Low-stock alerts.
- Search and filter.

### Member 3: Suppliers and Purchase

- Supplier CRUD.
- Purchase orders.
- Material receipt.
- Purchase-to-inventory update.

### Member 4: BOM and Production

- BOM creation and editing.
- Production order workflow.
- Material consumption.
- Finished-product inventory update.

### Member 5: Customers, Sales, and Reports

- Customer CRUD.
- Sales orders.
- Stock validation and deduction.
- PDF invoice.
- Excel export and QR code.

One coordinator should own the database schema, shared naming conventions, integration, and final workflow testing.

## 10. Recommended Build Order

1. Confirm the database schema and relationships.
2. Create the Flask project and MySQL connection.
3. Implement login and role checks.
4. Implement products, materials, suppliers, and customers.
5. Implement inventory and low-stock calculation.
6. Implement purchase order and material receipt workflow.
7. Implement BOM and production workflow.
8. Implement sales order and inventory deduction workflow.
9. Connect dashboard cards and charts to live database queries.
10. Add search, filters, notifications, and audit logs.
11. Add PDF invoice, Excel export, and QR/barcode.
12. Test the complete purchase-to-sales demonstration.
13. Prepare the final presentation and demo data.

## 11. Final Demonstration Flow

The judges should be shown one connected scenario:

1. Log in as a Manager.
2. Show the dashboard and current stock.
3. Add or select a supplier.
4. Create a purchase order for steel.
5. Mark the material as received.
6. Show that steel inventory increased.
7. Show the Gear Assembly BOM.
8. Create a production order for Gear Assemblies.
9. Complete production.
10. Show that raw materials decreased and finished-product stock increased.
11. Add or select a customer.
12. Create a sales order.
13. Demonstrate stock validation.
14. Process the sale and show finished-product stock decreased.
15. Generate the PDF invoice.
16. Show the dashboard charts, notification, QR/barcode, export option, and audit log.

This single flow demonstrates the most important integration marks: purchase, inventory, BOM, production, finished goods, sales, database updates, and reporting.

## 12. Testing Checklist

### Authentication

- [ ] Valid users can log in.
- [ ] Invalid credentials are rejected.
- [ ] Restricted actions are hidden or blocked by role.

### CRUD operations

- [ ] Add, view, edit, and delete/deactivate records.
- [ ] Required fields reject empty values.
- [ ] Duplicate IDs and invalid values are rejected.

### Inventory integration

- [ ] Purchase receipt increases raw material stock.
- [ ] Production completion decreases raw material stock.
- [ ] Production completion increases finished-product stock.
- [ ] Sales processing decreases finished-product stock.
- [ ] Negative stock is prevented.
- [ ] Low-stock alerts appear automatically.

### Reports and compulsory features

- [ ] PDF invoice contains correct customer, product, quantity, price, and total.
- [ ] Excel export contains current records.
- [ ] QR code or barcode contains a useful order or product reference.
- [ ] Charts display database values.
- [ ] Audit log records important actions.
- [ ] Search and filters return correct results.
- [ ] The layout works on desktop and mobile widths.

## 13. Definition of Done for the Competition Version

The project is ready for the competition when:

- Users can log in with different roles.
- The main records are stored in MySQL.
- The three major workflows work end to end:
  - Purchase -> material receipt -> inventory increase.
  - BOM -> production completion -> raw material deduction and finished stock increase.
  - Customer order -> stock check -> sale -> inventory reduction.
- The dashboard reads live data.
- The compulsory features are available or clearly demonstrated.
- The team can explain the database, backend routes, business rules, and frontend screens.
- The final demo can be completed reliably with prepared sample data.

## 14. Important Project Principle

The strongest version of this project is a simple ERP with real data flow:

```text
Working functionality > disconnected screens
Database integration > hardcoded values
Business workflows > visual decoration
Clear demonstration > unnecessary features
```

The target is not to reproduce every feature of a commercial ERP. The target is to demonstrate a believable, connected manufacturing ERP that solves the company's spreadsheet problem and proves the core business logic works.
