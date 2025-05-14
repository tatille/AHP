from flask import Blueprint, render_template, request, redirect, url_for, session

step2_bp = Blueprint("step2", __name__)

@step2_bp.route("/step2", methods=["GET", "POST"])
def step2():
    if request.method == "POST":
        num_criteria = session["num_criteria"]
        num_alternatives = session["num_alternatives"]

        criteria_names = []
        custom_criteria_names = []
        for i in range(num_criteria):
            name = request.form.get(f"criteria_name_{i}", "")
            if name == "Khác":
                custom_name = request.form.get(f"criteria_name_{i}_custom", "").strip()
                if not custom_name:
                    return render_template(
                        "step2.html",
                        error=f"Vui lòng nhập tên tiêu chí tùy chỉnh cho tiêu chí {i + 1}.",
                        num_criteria=num_criteria,
                        num_alternatives=num_alternatives,
                    )
                criteria_names.append(custom_name)  # Lưu tên tùy chỉnh thay vì "Khác"
                custom_criteria_names.append(custom_name)
            else:
                criteria_names.append(name)
                custom_criteria_names.append("")

        alternatives = []
        for i in range(num_alternatives):
            name = request.form.get(f"alternative_name_{i}", "")
            if name == "Khác":
                custom_name = request.form.get(f"alternative_name_{i}_custom", "").strip()
                if not custom_name:
                    return render_template(
                        "step2.html",
                        error=f"Vui lòng nhập tên phương án tùy chỉnh cho phương án {i + 1}.",
                        num_criteria=num_criteria,
                        num_alternatives=num_alternatives,
                    )
                alternatives.append(custom_name)  # Lưu tên tùy chỉnh thay vì "Khác"
            else:
                alternatives.append(name)

        session["criteria_names"] = criteria_names
        session["custom_criteria_names"] = custom_criteria_names
        session["alternatives"] = alternatives

        return redirect(url_for("step3.step3"))

    return render_template(
        "step2.html",
        num_criteria=session["num_criteria"],
        num_alternatives=session["num_alternatives"],
    )