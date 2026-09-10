SELECT product_id, product_name, unit_price, units_in_stock FROM northwind_products WHERE lower(product_name) LIKE '%' || lower('chai') || '%' ORDER BY product_id;
SELECT product_id, product_name, unit_price FROM northwind_products WHERE unit_price <= 10.00 AND discontinued = false ORDER BY unit_price, product_id LIMIT 5;
