from flask import Blueprint, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from excel_utils import export_to_excel, import_from_excel
from db_utils import save_to_history

excel_bp = Blueprint('excel', __name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@excel_bp.route('/export', methods=['POST'])
def export_excel():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Không có dữ liệu để xuất"}), 400
            
        # Lưu vào lịch sử trước khi xuất
        history_id = save_to_history(data)
        
        # Xuất ra Excel
        filename = export_to_excel(data)
        
        return send_file(
            filename,
            as_attachment=True,
            download_name=f"ahp_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@excel_bp.route('/import', methods=['POST'])
def import_excel():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Không tìm thấy file"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Không có file được chọn"}), 400
            
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({"error": "File không đúng định dạng Excel"}), 400
            
        # Lưu file tạm thời
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Đọc dữ liệu từ Excel
        data = import_from_excel(filepath)
        
        # Xóa file tạm
        os.remove(filepath)
        
        return jsonify({
            "status": "success",
            "data": data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500 