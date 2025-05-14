from flask import Flask, jsonify
import os
from dotenv import load_dotenv

# Import các blueprint từ thư mục routes
from routes.step1 import step1_bp
from routes.step2 import step2_bp
from routes.step3 import step3_bp
from routes.step4 import step4_bp
from routes.result import result_bp
from routes.history import history_bp
from routes.excel import excel_bp

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Đăng ký các blueprint
app.register_blueprint(step1_bp)
app.register_blueprint(step2_bp)
app.register_blueprint(step3_bp)
app.register_blueprint(step4_bp)
app.register_blueprint(result_bp)
app.register_blueprint(history_bp)
app.register_blueprint(excel_bp, url_prefix='/excel')

@app.errorhandler(Exception)
def handle_error(error):
    """Xử lý lỗi chung cho ứng dụng"""
    response = {
        "error": str(error),
        "status": "error"
    }
    return jsonify(response), 500

if __name__ == "__main__":
    app.run(debug=True)
