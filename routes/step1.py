from flask import Blueprint, render_template, request, redirect, url_for, session
import pandas as pd
from werkzeug.utils import secure_filename
import os
from excel_utils import import_from_excel

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
            if "file" not in request.files:
                return render_template("step1.html", error="Không tìm thấy file.")
            file = request.files["file"]
            if file.filename == "":
                return render_template("step1.html", error="Vui lòng chọn file.")
            if not file.filename.endswith((".xlsx", ".xls")):
                return render_template("step1.html", error="Chỉ hỗ trợ file Excel (.xlsx, .xls).")

            filename = secure_filename(file.filename)
            filepath = os.path.join("uploads", filename)
            file.save(filepath)

            try:
                data = import_from_excel(filepath)
                # Lưu dữ liệu vào session đúng chuẩn AHP
                session["criteria_names"] = data.get("criteria", [])
                session["criteria_weights"] = data.get("criteria_weights", [])
                session["alternatives"] = data.get("alternatives", [])
                session["alternative_weights"] = data.get("alternative_weights", [])
                # Nếu có thể, chuyển sang bước kết quả luôn
                os.remove(filepath)
                return redirect(url_for("result.result"))
            except Exception as e:
                return render_template("step1.html", error=f"Lỗi khi đọc file Excel: {e}")

    return render_template("step1.html")

@step1_bp.route("/upload_excel", methods=["POST"])
def upload_excel():
    if "file" not in request.files:
        return render_template("step1.html", error="Không tìm thấy file.")
    file = request.files["file"]
    if file.filename == "":
        return render_template("step1.html", error="Vui lòng chọn file.")
    if not file.filename.endswith(".xlsx"):
        return render_template("step1.html", error="Chỉ hỗ trợ file Excel (.xlsx).")

    filename = secure_filename(file.filename)
    filepath = os.path.join("uploads", filename)
    file.save(filepath)

    try:
        data = pd.read_excel(filepath)
        num_criteria = len(data.columns) - 1
        num_alternatives = len(data)
        if num_criteria < 3 or num_alternatives < 3:
            return render_template("step1.html", error="Số lượng tiêu chí và phương án tối thiểu là 3.")
        if num_criteria > 10 or num_alternatives > 10:
            return render_template("step1.html", error="Số lượng tiêu chí và phương án tối đa là 10.")
        session["num_criteria"] = num_criteria
        session["num_alternatives"] = num_alternatives
        session["criteria_names"] = data.columns[1:].tolist()
        session["alternatives"] = data.iloc[:, 0].tolist()
        session["criteria_matrix"] = data.iloc[:, 1:].values.tolist()
        return redirect(url_for("step2.step2"))
    except Exception as e:
        return render_template("step1.html", error=f"Lỗi khi đọc file Excel: {e}")