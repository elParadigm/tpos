from database import get_db

def log_action(action_type, description, worker_name=None, worker_id=None):
    """
    Logs an audit event to the database.
    action_type: 'SALE', 'STOCK', 'PRODUCT', 'SETTINGS', etc.
    worker_name: display name of the worker (passed directly)
    worker_id: lookup the worker name from the database if worker_name not provided
    """
    db = get_db()
    try:
        # Lookup worker name from ID if name not given directly
        if not worker_name and worker_id:
            row = db.execute(
                "SELECT name FROM workers WHERE id = ?", [worker_id]
            ).fetchone()
            worker_name = row['name'] if row else None

        db.execute(
            "INSERT INTO audit_logs (action_type, description, worker_name) VALUES (?, ?, ?)",
            (action_type, description, worker_name)
        )
        db.commit()
    except Exception as e:
        print(f"Error writing audit log: {e}")
    finally:
        db.close()
