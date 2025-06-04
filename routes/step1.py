from flask import Blueprint, render_template, request, redirect, url_for, session, send_file
import pandas as pd
from werkzeug.utils import secure_filename
import os
from excel_utils import import_from_excel, create_template_excel

step1_bp = Blueprint("step1", __name__)

@step1_bp.route("/", methods=["GET", "POST"])
def step1():
    if request.method == "POST":
        input_method = request.form.get("input_method")

        if input_method == "manual":
            try:
                num_criteria = int(request.form["num_criteria"])
                num_alternatives = int(request.form["num_alternatives"])
                if num_criteria < 3 or num_alternatives < 3:
                    return render_template("step1.html", error="Số lượng tiêu chí và phương án tối thiểu là 3.")
                if num_criteria > 10 or num_alternatives > 10:
                    return render_template("step1.html", error="Số lượng tiêu chí và phương án tối đa là 10.")
            except ValueError as e:
                return render_template("step1.html", error=str(e))

            session["num_criteria"] = num_criteria
            session["num_alternatives"] = num_alternatives
            session["criteria_names"] = [""] * num_criteria
            session["alternatives"] = [""] * num_alternatives

            return redirect(url_for("step2.step2"))

        elif input_method == "excel":
            print("Xử lý nhập liệu từ file Excel...")
            if "file" not in request.files:
                print("Lỗi: Không tìm thấy file trong request.")
                return render_template("step1.html", error="Không tìm thấy file.")
            file = request.files['file']
            if file.filename == "":
                print("Lỗi: Không có file được chọn.")
                return render_template("step1.html", error="Vui lòng chọn file.")
            if not file.filename.endswith((".xlsx", ".xls")):
                print("Lỗi: File không đúng định dạng Excel.")
                return render_template("step1.html", error="Chỉ hỗ trợ file Excel (.xlsx, .xls).")

            filename = secure_filename(file.filename)
            filepath = os.path.join("uploads", filename)
            print(f"Lưu file tạm thời tại: {filepath}")
            os.makedirs("uploads", exist_ok=True)
            file.save(filepath)

            try:
                print(f"Gọi hàm import_from_excel với file: {filepath}")
                data = import_from_excel(filepath)
                print("Import thành công.")
                # Lưu dữ liệu vào session
                print("Lưu dữ liệu vào session...")
                session["criteria_names"] = data["criteria"]
                session["criteria_weights"] = data["criteria_weights"]
                session["alternatives"] = data["alternatives"]
                session["alternative_weights"] = data["alternative_weights"]
                session["num_criteria"] = len(data["criteria"])
                session["num_alternatives"] = len(data["alternatives"])
                session["criteria_matrix"] = data["criteria_matrix"]
                session["alternative_matrices"] = data["alternative_matrices"]
                print("Đã lưu dữ liệu vào session.")
                
                # Xóa file tạm
                print(f"Xóa file tạm: {filepath}")
                os.remove(filepath)
                print("Đã xóa file tạm.")
                
                # Chuyển sang trang kết quả
                print("Chuyển hướng đến trang kết quả...")
                return redirect(url_for("result.result"))
            except Exception as e:
                print(f"Lỗi trong quá trình xử lý file Excel: {str(e)}")
                import traceback
                print(f"Stack trace: {traceback.format_exc()}")
                if os.path.exists(filepath):
                    print(f"Xóa file tạm sau lỗi: {filepath}")
                    os.remove(filepath)
                return render_template("step1.html", error=f"Lỗi xử lý file Excel: {str(e)}")

    return render_template("step1.html")

@step1_bp.route("/download_template")
def download_template():
    """Tải xuống template Excel mẫu"""
    try:
        # Tạo template file
        template_path = create_template_excel()
        
        # Kiểm tra file tồn tại
        if not os.path.exists(template_path):
            raise FileNotFoundError("Không tìm thấy file template")
            
        # Gửi file cho người dùng
        return send_file(
            template_path,
            as_attachment=True,
            download_name="ahp_template.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return render_template("step1.html", error=f"Lỗi khi tải template: {str(e)}")