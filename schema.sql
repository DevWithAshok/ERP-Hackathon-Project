-- Manufacturing ERP database schema.
-- Select the target database first, then run this file in MySQL Workbench or with the MySQL client.

CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('Administrator', 'Manager', 'Employee') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS products (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(40) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    selling_price DECIMAL(12, 2) NOT NULL DEFAULT 0,
    description TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_products_price CHECK (selling_price >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS suppliers (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(40) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    email VARCHAR(150) NOT NULL,
    address VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS customers (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(40) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    email VARCHAR(150) NOT NULL,
    address VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS materials (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(40) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    minimum_stock DECIMAL(12, 3) NOT NULL DEFAULT 0,
    supplier_id INT UNSIGNED NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_material_minimum_stock CHECK (minimum_stock >= 0),
    CONSTRAINT fk_material_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
) ENGINE=InnoDB;

-- One inventory row represents either raw material or finished product stock.
CREATE TABLE IF NOT EXISTS inventory (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    material_id INT UNSIGNED NULL UNIQUE,
    product_id INT UNSIGNED NULL UNIQUE,
    quantity DECIMAL(12, 3) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_inventory_one_item CHECK (
        (material_id IS NOT NULL AND product_id IS NULL)
        OR (material_id IS NULL AND product_id IS NOT NULL)
    ),
    CONSTRAINT chk_inventory_quantity CHECK (quantity >= 0),
    CONSTRAINT fk_inventory_material FOREIGN KEY (material_id) REFERENCES materials(id),
    CONSTRAINT fk_inventory_product FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS purchase_orders (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(40) NOT NULL UNIQUE,
    supplier_id INT UNSIGNED NOT NULL,
    status ENUM('Draft', 'Ordered', 'Received', 'Cancelled') NOT NULL DEFAULT 'Draft',
    order_date DATE NOT NULL,
    received_at DATETIME NULL,
    created_by INT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_purchase_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    CONSTRAINT fk_purchase_creator FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_purchase_status (status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS purchase_order_items (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    purchase_order_id INT UNSIGNED NOT NULL,
    material_id INT UNSIGNED NOT NULL,
    quantity DECIMAL(12, 3) NOT NULL,
    unit_price DECIMAL(12, 2) NOT NULL DEFAULT 0,
    CONSTRAINT chk_purchase_item_quantity CHECK (quantity > 0),
    CONSTRAINT chk_purchase_item_price CHECK (unit_price >= 0),
    CONSTRAINT fk_purchase_item_order FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
    CONSTRAINT fk_purchase_item_material FOREIGN KEY (material_id) REFERENCES materials(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS bom_headers (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    product_id INT UNSIGNED NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bom_product FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS bom_items (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    bom_id INT UNSIGNED NOT NULL,
    material_id INT UNSIGNED NOT NULL,
    quantity_per_unit DECIMAL(12, 3) NOT NULL,
    CONSTRAINT uq_bom_material UNIQUE (bom_id, material_id),
    CONSTRAINT chk_bom_quantity CHECK (quantity_per_unit > 0),
    CONSTRAINT fk_bom_item_header FOREIGN KEY (bom_id) REFERENCES bom_headers(id),
    CONSTRAINT fk_bom_item_material FOREIGN KEY (material_id) REFERENCES materials(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS production_orders (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(40) NOT NULL UNIQUE,
    product_id INT UNSIGNED NOT NULL,
    quantity DECIMAL(12, 3) NOT NULL,
    status ENUM('Pending', 'In Progress', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Pending',
    created_by INT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL,
    CONSTRAINT chk_production_quantity CHECK (quantity > 0),
    CONSTRAINT fk_production_product FOREIGN KEY (product_id) REFERENCES products(id),
    CONSTRAINT fk_production_creator FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_production_status (status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sales_orders (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(40) NOT NULL UNIQUE,
    customer_id INT UNSIGNED NOT NULL,
    status ENUM('Pending', 'Confirmed', 'Processed', 'Cancelled') NOT NULL DEFAULT 'Pending',
    order_date DATE NOT NULL,
    created_by INT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME NULL,
    CONSTRAINT fk_sales_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT fk_sales_creator FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_sales_status (status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sales_order_items (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sales_order_id INT UNSIGNED NOT NULL,
    product_id INT UNSIGNED NOT NULL,
    quantity DECIMAL(12, 3) NOT NULL,
    unit_price DECIMAL(12, 2) NOT NULL,
    CONSTRAINT chk_sales_item_quantity CHECK (quantity > 0),
    CONSTRAINT chk_sales_item_price CHECK (unit_price >= 0),
    CONSTRAINT fk_sales_item_order FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id),
    CONSTRAINT fk_sales_item_product FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS stock_movements (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    material_id INT UNSIGNED NULL,
    product_id INT UNSIGNED NULL,
    quantity_change DECIMAL(12, 3) NOT NULL,
    reason ENUM('Purchase Receipt', 'Production Consumption', 'Production Output', 'Sales Processing', 'Adjustment') NOT NULL,
    source_type VARCHAR(50) NULL,
    source_id INT UNSIGNED NULL,
    created_by INT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_movement_material FOREIGN KEY (material_id) REFERENCES materials(id),
    CONSTRAINT fk_movement_product FOREIGN KEY (product_id) REFERENCES products(id),
    CONSTRAINT fk_movement_creator FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_movement_created_at (created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS notifications (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NULL,
    title VARCHAR(150) NOT NULL,
    message VARCHAR(500) NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notification_user FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_notification_read (is_read)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(80) NOT NULL,
    entity_id INT UNSIGNED NULL,
    details JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_audit_created_at (created_at)
) ENGINE=InnoDB;
