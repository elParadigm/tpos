from flask import Flask
from flask_cors import CORS
from database import init_db
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
from routes.backup import backup_bp

app = Flask(__name__)
CORS(app)

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

init_db()

if __name__ == '__main__':
    app.run(debug=True)
