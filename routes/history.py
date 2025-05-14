from flask import Blueprint, render_template, redirect, url_for, send_file
from db_utils import get_db
import pandas as pd
import os

history_bp = Blueprint("history", __name__)

db = get_db()
history_collection = db["ahp_history"]

@history_bp.route("/history")
def history():
    records = list(history_collection.find().sort("timestamp", -1))
    for record in records:
        record["criteria_names"] = record.get("criteria_names", [])
        record["alternative_matrices"] = record.get("alternative_matrices", [])
    return render_template("history.html", records=records)

@history_bp.route("/clear_history", methods=["POST"])
def clear_history():
    history_collection.delete_many({})
    return redirect(url_for("history.history"))

@history_bp.route("/export_history", methods=["GET"])
def export_history():
    records = list(history_collection.find().sort("timestamp", -1))
    if not records:
        return redirect(url_for("history.history"))

    # Tạo DataFrame từ lịch sử
    data = []
    for record in records:
        data.append({
            "Thời gian": record.get("timestamp"),
            "CR": record.get("CR"),
            "Tiêu chí": ", ".join(record.get("criteria_names", [])),
            "Phương án": ", ".join(record.get("alternatives", [])),
            "Xếp hạng": ", ".join(
                [f"{alt} ({score:.4f})" for alt, score in record.get("ranked_alternatives", [])]
            ),
        })

    df = pd.DataFrame(data)

    # Ghi vào file Excel
    filepath = "history_output.xlsx"
    df.to_excel(filepath, index=False)

    return send_file(filepath, as_attachment=True, download_name="history_output.xlsx")