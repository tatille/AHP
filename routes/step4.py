from flask import Blueprint, render_template, request, redirect, url_for, session
from fractions import Fraction
import numpy as np
from ahp_utils import calculate_weights

step4_bp = Blueprint("step4", __name__)

@step4_bp.route("/step4", methods=["GET", "POST"])
def step4():
    if request.method == "POST":
        try:
            num_criteria = session["num_criteria"]
            num_alternatives = session["num_alternatives"]
            alternative_matrices = session.get("alternative_matrices", [])
            errors = []

            for i in range(num_criteria):
                matrix = alternative_matrices[i] if i < len(alternative_matrices) else [
                    [1.0 if j == k else None for k in range(num_alternatives)] for j in range(num_alternatives)
                ]

                for j in range(num_alternatives):
                    for k in range(j + 1, num_alternatives):
                        value = request.form.get(f"alternative_{i}_{j}_{k}", "").strip()
                        if not value:
                            # Sử dụng giá trị gợi ý mặc định nếu không có giá trị nhập
                            value = "1"
                        try:
                            val = float(Fraction(value))  # Hỗ trợ dạng "1/3"
                            matrix[j][k] = val
                            matrix[k][j] = round(1 / val, 5)  # Tính nghịch đảo
                        except Exception:
                            errors.append(f"Giá trị không hợp lệ tại tiêu chí {session['criteria_names'][i]}, cặp ({session['alternatives'][j]}, {session['alternatives'][k]}): {value}")

                if i < len(alternative_matrices):
                    alternative_matrices[i] = matrix
                else:
                    alternative_matrices.append(matrix)

            session["alternative_matrices"] = alternative_matrices

            # Kiểm tra hợp lệ từng ma trận phương án (CR <= 0.1)
            cr_list = []
            for i, matrix in enumerate(alternative_matrices):
                try:
                    weights, CR = calculate_weights(matrix)
                    cr_list.append(CR)
                    if CR > 0.1:
                        errors.append(f"Ma trận phương án cho tiêu chí '{session['criteria_names'][i]}' có chỉ số nhất quán CR = {CR:.4f} vượt ngưỡng cho phép (0.1). Vui lòng điều chỉnh lại.")
                except Exception as e:
                    cr_list.append(None)
                    errors.append(f"Lỗi tính toán ma trận phương án cho tiêu chí '{session['criteria_names'][i]}': {e}")

            # Lưu lại CR cho từng ma trận để hiển thị lại trên giao diện
            session['alternative_cr_list'] = cr_list

            if errors:
                return render_template(
                    "step4.html",
                    error="Có lỗi trong dữ liệu nhập: " + "; ".join(errors),
                    num_criteria=num_criteria,
                    num_alternatives=num_alternatives,
                    criteria_names=session["criteria_names"],
                    alternatives=session["alternatives"],
                    alternative_matrices=alternative_matrices,
                    alternative_cr_list=cr_list,
                    enumerate=enumerate
                )

            return redirect(url_for("result.result"))

        except Exception as e:
            return render_template(
                "step4.html",
                error=f"Lỗi: {e}",
                num_criteria=session["num_criteria"],
                num_alternatives=session["num_alternatives"],
                criteria_names=session["criteria_names"],
                alternatives=session["alternatives"],
                alternative_matrices=session.get("alternative_matrices", []),
                enumerate=enumerate
            )

    if "alternative_matrices" not in session:
        num_criteria = session["num_criteria"]
        num_alternatives = session["num_alternatives"]
        session["alternative_matrices"] = [
            [[1 if j == k else "1" for k in range(num_alternatives)] for j in range(num_alternatives)]
            for _ in range(num_criteria)
        ]

    return render_template(
        "step4.html",
        num_criteria=session["num_criteria"],
        num_alternatives=session["num_alternatives"],
        criteria_names=session["criteria_names"],
        alternatives=session["alternatives"],
        alternative_matrices=session["alternative_matrices"],
        alternative_cr_list=session.get('alternative_cr_list', []),
        enumerate=enumerate
    )
