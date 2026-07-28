from database import get_db

def log_action(action_type, description, worker_name=None):
    """
    Logs an audit event to the database.
    action_type: 'SALE', 'STOCK_UPDATE', 'PRODUCT_CREATE', 'PRODUCT_UPDATE', 'SETTINGS_UPDATE', 'SHIFT', etc.
    """
    try:
        db = get_db()
        # Ensure audit_logs table exists
        db.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                description TEXT NOT NULL,
                worker_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute(
            "INSERT INTO audit_logs (action_type, description, worker_name) VALUES (?, ?, ?)",
            (action_type, description, worker_name)
        )
        db.commit()
    except Exception as e:
        print(f"Error writing audit log: {e}")
