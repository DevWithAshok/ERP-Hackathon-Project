-- Demo data for the manufacturing ERP.
-- Run schema.sql before running this file.

-- Passwords are stored as Werkzeug scrypt hashes, never as plain text.
INSERT INTO users (username, password_hash, role)
VALUES
    ('admin', 'scrypt:32768:8:1$YOHfNvbi5YQAkSeq$fb1b470bc81789aea811cd5645bd58f1646769ff612b3ef64a093ca2bccecfc7a6b0699aa93678de036aac9dc98852fbf223db0b2d35985ce86a19f21d199241', 'Administrator'),
    ('manager', 'scrypt:32768:8:1$ghbPJOlB5whmV2cN$3c81b794a0ef81bbc319a0401ab78946920aa679aade801da9f0ca16c34d40d2b6bffd1ac0de8324dab6aea0edf6b4680dc74530e98816890f08379e61c4f75f', 'Manager'),
    ('employee', 'scrypt:32768:8:1$sqadYKl1IwbobGNi$e53f99981ef3285839d64a38eb3ea74275e9dd6cb260133973ab238680dbb12d00060cc17c1dfda0b4ae84ab08541e939a3e95a6f6782034c074254c017aaab7', 'Employee')
ON DUPLICATE KEY UPDATE username = VALUES(username);

INSERT INTO suppliers (code, name, phone, email, address)
VALUES ('SUP-001', 'ABC Metals', '9876543210', 'sales@abcmetals.example', 'Industrial Area')
ON DUPLICATE KEY UPDATE code = VALUES(code);

INSERT INTO customers (code, name, phone, email, address)
VALUES ('CUS-001', 'XYZ Machines', '9876501234', 'purchase@xyzmachines.example', 'Manufacturing Park')
ON DUPLICATE KEY UPDATE code = VALUES(code);

INSERT INTO products (code, name, category, selling_price, description)
VALUES ('FG-001', 'Gear Assembly', 'Mechanical', 2500.00, 'Finished gear assembly for industrial equipment')
ON DUPLICATE KEY UPDATE code = VALUES(code);

INSERT INTO materials (code, name, category, unit, minimum_stock, supplier_id)
SELECT 'RM-001', 'Steel', 'Metal', 'kg', 50.000, id
FROM suppliers WHERE code = 'SUP-001'
ON DUPLICATE KEY UPDATE code = VALUES(code);

INSERT INTO materials (code, name, category, unit, minimum_stock, supplier_id)
SELECT 'RM-002', 'Key', 'Component', 'Nos', 20.000, id
FROM suppliers WHERE code = 'SUP-001'
ON DUPLICATE KEY UPDATE code = VALUES(code);

INSERT INTO materials (code, name, category, unit, minimum_stock, supplier_id)
SELECT 'RM-003', 'Bearing', 'Component', 'No', 10.000, id
FROM suppliers WHERE code = 'SUP-001'
ON DUPLICATE KEY UPDATE code = VALUES(code);

INSERT INTO inventory (material_id, quantity)
SELECT id, CASE code
    WHEN 'RM-001' THEN 100.000
    WHEN 'RM-002' THEN 40.000
    WHEN 'RM-003' THEN 20.000
END
FROM materials
WHERE code IN ('RM-001', 'RM-002', 'RM-003')
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

INSERT INTO inventory (product_id, quantity)
SELECT id, 0.000 FROM products WHERE code = 'FG-001'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

INSERT INTO bom_headers (product_id)
SELECT id FROM products WHERE code = 'FG-001'
ON DUPLICATE KEY UPDATE product_id = VALUES(product_id);

INSERT INTO bom_items (bom_id, material_id, quantity_per_unit)
SELECT bom.id, material.id, requirements.quantity_per_unit
FROM bom_headers bom
JOIN products product ON product.id = bom.product_id
JOIN (
    SELECT 'RM-001' AS code, 5.000 AS quantity_per_unit
    UNION ALL SELECT 'RM-002', 2.000
    UNION ALL SELECT 'RM-003', 1.000
) requirements
JOIN materials material ON material.code = requirements.code
WHERE product.code = 'FG-001'
ON DUPLICATE KEY UPDATE quantity_per_unit = VALUES(quantity_per_unit);

-- Verify the main demo records after import.
SELECT username, role FROM users ORDER BY id;
SELECT code, name FROM products;
SELECT code, name, minimum_stock FROM materials ORDER BY code;
SELECT product.code AS product_code, material.code AS material_code, bom_item.quantity_per_unit
FROM bom_items bom_item
JOIN bom_headers bom ON bom.id = bom_item.bom_id
JOIN products product ON product.id = bom.product_id
JOIN materials material ON material.id = bom_item.material_id
ORDER BY bom_item.id;
