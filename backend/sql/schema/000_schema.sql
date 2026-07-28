-- ============================================================
--  POS SYSTEM - FULL SCHEMA
--  File: 000_schema.sql
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ------------------------------------------------------------
-- 1. CATEGORIES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT
);

-- ------------------------------------------------------------
-- 2. SUPPLIERS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    phone   TEXT,
    address TEXT,
    notes   TEXT
);

-- ------------------------------------------------------------
-- 3. CUSTOMERS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    phone      TEXT,
    notes      TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 4. WORKERS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS workers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    phone      TEXT,
    role       TEXT CHECK(role IN ('cashier', 'manager')),
    pin        TEXT NOT NULL,
    is_active  INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 5. PRODUCTS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    barcode     TEXT    PRIMARY KEY,
    name        TEXT    NOT NULL,
    category_id INTEGER,
    cost_price  REAL    NOT NULL DEFAULT 0,
    sell_price  REAL    NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 0,
    min_stock   INTEGER NOT NULL DEFAULT 5,
    is_active   INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- ------------------------------------------------------------
-- 6. DELIVERIES  (one per supplier invoice)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deliveries (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id   INTEGER,
    delivery_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    amount_due    REAL NOT NULL DEFAULT 0,
    amount_paid   REAL NOT NULL DEFAULT 0,
    due_date      DATE,
    notes         TEXT,
    created_by    INTEGER,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (created_by)  REFERENCES workers(id)
);

-- ------------------------------------------------------------
-- 7. DELIVERY ITEMS  (products in each delivery)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS delivery_items (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_id          INTEGER NOT NULL,
    barcode              TEXT    NOT NULL,
    quantity             INTEGER NOT NULL,
    cost_price           REAL    NOT NULL,
    suggested_sell_price REAL,
    FOREIGN KEY (delivery_id) REFERENCES deliveries(id) ON DELETE CASCADE,
    FOREIGN KEY (barcode)     REFERENCES products(barcode)
);

-- ------------------------------------------------------------
-- 8. SUPPLIER PAYMENTS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS supplier_payments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_id INTEGER NOT NULL,
    amount      REAL    NOT NULL,
    paid_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes       TEXT,
    created_by  INTEGER,
    FOREIGN KEY (delivery_id) REFERENCES deliveries(id),
    FOREIGN KEY (created_by)  REFERENCES workers(id)
);

-- ------------------------------------------------------------
-- 9. CUSTOMER PAYMENTS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customer_payments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    amount      REAL    NOT NULL,
    paid_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes       TEXT,
    created_by  INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (created_by)  REFERENCES workers(id)
);

-- ------------------------------------------------------------
-- 10. SALES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sales (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_date      DATETIME DEFAULT CURRENT_TIMESTAMP,
    total          REAL    NOT NULL,
    discount       REAL    NOT NULL DEFAULT 0,
    payment_method TEXT    DEFAULT 'cash'
                           CHECK(payment_method IN ('cash', 'check', 'credit')),
    customer_id    INTEGER,
    notes          TEXT,
    created_by     INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (created_by)  REFERENCES workers(id)
);

-- ------------------------------------------------------------
-- 11. SALE ITEMS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sale_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id     INTEGER NOT NULL,
    barcode     TEXT,
    custom_name TEXT,
    custom_cost REAL,
    quantity    INTEGER NOT NULL,
    unit_price  REAL    NOT NULL,
    discount    REAL    NOT NULL DEFAULT 0,
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY (barcode) REFERENCES products(barcode),
    CHECK (barcode IS NOT NULL OR custom_name IS NOT NULL)
);

-- ------------------------------------------------------------
-- 12. SETTINGS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- ------------------------------------------------------------
-- INDEXES
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_products_category        ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_active          ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_deliveries_supplier      ON deliveries(supplier_id);
CREATE INDEX IF NOT EXISTS idx_delivery_items_delivery  ON delivery_items(delivery_id);
CREATE INDEX IF NOT EXISTS idx_delivery_items_barcode   ON delivery_items(barcode);
CREATE INDEX IF NOT EXISTS idx_supplier_payments_delivery ON supplier_payments(delivery_id);
CREATE INDEX IF NOT EXISTS idx_customer_payments_customer ON customer_payments(customer_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_sale          ON sale_items(sale_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_barcode       ON sale_items(barcode);
CREATE INDEX IF NOT EXISTS idx_sales_date               ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_customer           ON sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_worker             ON sales(created_by);

-- ------------------------------------------------------------
-- DEFAULT SETTINGS SEED
-- ------------------------------------------------------------
INSERT OR IGNORE INTO settings (key, value) VALUES
    ('store_name',      'Mon Magasin'),
    ('receipt_header',  ''),
    ('printer_port',    '/dev/usb/lp0'),
    ('printer_enabled', '0'),
    ('currency',        'DT');
