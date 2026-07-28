-- add pin to workers
ALTER TABLE workers ADD COLUMN pin TEXT;

-- add created_by to affected tables
ALTER TABLE sales ADD COLUMN created_by INTEGER REFERENCES workers(id);
ALTER TABLE stock_entries ADD COLUMN created_by INTEGER REFERENCES workers(id);
ALTER TABLE customer_payments ADD COLUMN created_by INTEGER REFERENCES workers(id);
ALTER TABLE supplier_payments ADD COLUMN created_by INTEGER REFERENCES workers(id);

-- drop shifts
DROP TABLE IF EXISTS shifts;
