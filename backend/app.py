import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from auth import verify_token
from database import init_db

# Built SvelteKit SPA is copied here (see tools/tpos-kiosk-setup.sh and
# frontend build docs). This is what the kiosk browser actually loads.
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
from routes.categories import categories_bp
from routes.suppliers import suppliers_bp
from routes.products import products_bp
from routes.stock import stock_bp
from routes.customers import customers_bp
from routes.workers import workers_bp
from routes.sales import sales_bp
from routes.analytics import analytics_bp
from routes.settings import settings_bp
from routes.history import history_bp
from routes.backup import backup_bp, ensure_autobackup_started
from routes.system import system_bp
from routes.reports import reports_bp

app = Flask(__name__)

# The frontend and API are served from the same origin, so browsers never
# send cross-origin requests. Restrict CORS to that same origin anyway so a
# malicious page loaded in the kiosk cannot call the API cross-origin.
# CORS is restricted to the kiosk origin (the SPA is served same-origin from
# Flask) plus the Vite dev server origins so `npm run dev` works. Override
# with TPOS_ORIGIN if the app is served from a different host/port.
_cors_origins = os.environ.get(
    'TPOS_ORIGIN',
    'http://localhost:5000 http://127.0.0.1:5000 '
    'http://localhost:5173 http://127.0.0.1:5173'
).split()
CORS(app, resources={r"/api/*": {"origins": _cors_origins}})

app.register_blueprint(categories_bp, url_prefix='/api')
app.register_blueprint(suppliers_bp,  url_prefix='/api')
app.register_blueprint(products_bp,   url_prefix='/api')
app.register_blueprint(stock_bp,      url_prefix='/api')
app.register_blueprint(customers_bp,  url_prefix='/api')
app.register_blueprint(workers_bp,    url_prefix='/api')
app.register_blueprint(sales_bp,      url_prefix='/api')
app.register_blueprint(analytics_bp,  url_prefix='/api')
app.register_blueprint(settings_bp,   url_prefix='/api')
app.register_blueprint(history_bp,    url_prefix='/api')
app.register_blueprint(backup_bp,     url_prefix='/api')
app.register_blueprint(system_bp,     url_prefix='/api')
app.register_blueprint(reports_bp,    url_prefix='/api')


@app.before_request
def _require_auth():
    """All /api requests require a valid session token (X-Auth-Token).

    Exceptions: /workers/login (the entry point) and OPTIONS preflight.
    Fine-grained permission checks live in each route (login_required /
    manager_required decorators); this hook is the outer gate.
    """
    if not request.path.startswith('/api'):
        return None
    if request.method == 'OPTIONS':
        return None
    if request.path == '/api/workers/login':
        return None
    token = request.headers.get('X-Auth-Token', '')
    if not verify_token(token):
        return jsonify({'error': 'Non autorisé. Veuillez vous reconnecter.'}), 401
    return None


@app.errorhandler(404)
def _not_found(_):
    if request.path.startswith('/api'):
        return jsonify({'error': 'Not found'}), 404
    return None


@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')


@app.route('/<path:path>')
def static_files(path):
    """Serve the SPA build. Anything outside /api resolves to a static
    file if it exists, otherwise falls back to index.html (client routes)."""
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    full = os.path.join(STATIC_DIR, path)
    if os.path.isfile(full):
        return send_from_directory(STATIC_DIR, path)
    return send_from_directory(STATIC_DIR, 'index.html')


init_db()
ensure_autobackup_started()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
