from flask import Blueprint, render_template, request, redirect, url_for, session
from fractions import Fraction
import numpy as np

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

            if errors:
                return render_template(
                    "step4.html",
                    error="Có lỗi trong dữ liệu nhập: " + "; ".join(errors),
                    num_criteria=num_criteria,
                    num_alternatives=num_alternatives,
                    criteria_names=session["criteria_names"],
                    alternatives=session["alternatives"],
                    alternative_matrices=alternative_matrices,
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
        enumerate=enumerate
    )
