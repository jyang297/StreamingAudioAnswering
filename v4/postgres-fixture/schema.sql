DROP TABLE IF EXISTS northwind_products;
CREATE TABLE northwind_products (
  product_id integer PRIMARY KEY,
  product_name text NOT NULL,
  supplier_id integer NOT NULL,
  category_id integer NOT NULL,
  quantity_per_unit text NOT NULL,
  unit_price numeric(10,2) NOT NULL,
  units_in_stock integer NOT NULL,
  units_on_order integer NOT NULL,
  reorder_level integer NOT NULL,
  discontinued boolean NOT NULL
);
CREATE INDEX northwind_products_name_lower_idx ON northwind_products (lower(product_name));
