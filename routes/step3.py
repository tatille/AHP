from flask import Blueprint, render_template, request, redirect, url_for, session
from fractions import Fraction
import numpy as np
from ahp_utils import calculate_weights

step3_bp = Blueprint("step3", __name__)

@step3_bp.route("/step3", methods=["GET", "POST"])
def step3():
    # Kiểm tra nếu "num_criteria" không tồn tại trong session
    if "num_criteria" not in session:
        return redirect(url_for("step1.step1"))  # Chuyển hướng về bước 1

    num_criteria = session["num_criteria"]

    if request.method == "POST":
        criteria_matrix = []
        for i in range(num_criteria):
            row = []
            for j in range(num_criteria):
                if i == j:
                    row.append(1)
                elif i < j:
                    value = request.form.get(f"criteria_{i}_{j}")
                    row.append(value)
                else:
                    value = 1 / float(Fraction(criteria_matrix[j][i]))
                    row.append(value)
            criteria_matrix.append(row)

        try:
            criteria_matrix = [
                [float(Fraction(value)) if isinstance(value, str) and '/' in value else float(value)
                 for value in row]
                for row in criteria_matrix
            ]
        except ValueError as e:
            return render_template("step3.html", error=f"Lỗi dữ liệu: {e}", num_criteria=num_criteria)
        except Exception as e:
            return render_template("step3.html", error=f"Lỗi không xác định: {e}", num_criteria=num_criteria)

        try:
            weights, CR = calculate_weights(np.array(criteria_matrix))
            if CR > 0.1:
                return render_template(
                    "step3.html",
                    error=f"CR = {CR:.4f} vượt ngưỡng cho phép (0.1). Vui lòng điều chỉnh ma trận.",
                    num_criteria=num_criteria,
                    criteria_names=session["criteria_names"],
                    criteria_matrix=session["criteria_matrix"],
                )
        except Exception as e:
            return render_template("step3.html", error=f"Lỗi: {e}", num_criteria=num_criteria)

        session["criteria_matrix"] = criteria_matrix
        session["criteria_weights"] = weights.tolist()

        return redirect(url_for("step4.step4"))

    if "criteria_matrix" not in session:
        session["criteria_matrix"] = [
            ["1" if i == j else "" for j in range(num_criteria)]
            for i in range(num_criteria)
        ]

    return render_template(
        "step3.html",
        num_criteria=num_criteria,
        criteria_names=session["criteria_names"],
        criteria_matrix=session["criteria_matrix"],
    )