from flask import Blueprint, render_template, session, redirect, url_for, send_file, make_response, render_template_string
import numpy as np
import pandas as pd
from ahp_utils import calculate_weights, calculate_details
from fractions import Fraction
from datetime import datetime
from db_utils import get_db
import matplotlib.pyplot as plt
import io
import base64
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import os

result_bp = Blueprint("result", __name__)

@result_bp.route("/result")
def result():
    try:
        # Lấy dữ liệu từ session
        criteria_matrix = session.get("criteria_matrix")
        alternative_matrices = session.get("alternative_matrices")

        # Kiểm tra dữ liệu
        if not criteria_matrix:
            raise ValueError("Ma trận tiêu chí bị thiếu.")
        if not alternative_matrices:
            raise ValueError("Ma trận phương án bị thiếu.")

        # Chuyển đổi dữ liệu từ session
        criteria_matrix = [
            [float(Fraction(value)) if isinstance(value, str) and '/' in value else float(value)
             for value in row]
            for row in criteria_matrix
        ]

        alternative_matrices = [
            [
                [float(Fraction(value)) if isinstance(value, str) and '/' in value else float(value)
                 for value in row]
                for row in matrix
            ]
            for matrix in alternative_matrices
        ]

        # Tính toán chi tiết cho ma trận tiêu chí
        criteria_details = calculate_details(criteria_matrix)
        # Tính toán trọng số và xếp hạng
        weights, CR = criteria_details['weights'], criteria_details['CR']
        alternative_weights = {
            session["criteria_names"][i]: calculate_weights(np.array(matrix))[0]
            for i, matrix in enumerate(alternative_matrices)
        }
        alternative_weights_matrix = np.array(list(alternative_weights.values())).T
        overall_scores = np.dot(weights, alternative_weights_matrix)
        ranked_alternatives = [
            (session["alternatives"][i], score)
            for i, score in enumerate(overall_scores)
        ]
        ranked_alternatives.sort(key=lambda x: x[1], reverse=True)

        # Tính toán chi tiết cho từng ma trận phương án
        alternatives_details = []
        for i, matrix in enumerate(alternative_matrices):
            details = calculate_details(matrix)
            alternatives_details.append({
                'name': session['criteria_names'][i],
                'details': details,
                'alternatives': session['alternatives']
            })

        # Lưu lại vào session để các route export dùng được
        session["criteria_weights"] = weights.tolist()
        session["ranked_alternatives"] = ranked_alternatives

        # Chuẩn bị kết quả
        result = {
            "CR": CR,
            "weights": {session["criteria_names"][i]: weights[i] for i in range(len(weights))},
            "alternative_weights": alternative_weights,
            "ranked_alternatives": ranked_alternatives,
            "criteria_details": criteria_details,
            "criteria_names": session["criteria_names"],
            "alternatives": session["alternatives"],
            "alternatives_details": alternatives_details
        }

        # Lưu lịch sử vào MongoDB
        db = get_db()
        history_collection = db["ahp_history"]
        history_collection.insert_one({
            "timestamp": datetime.now(),
            "criteria_names": session["criteria_names"],
            "alternatives": session["alternatives"],
            "criteria_matrix": session["criteria_matrix"],
            "alternative_matrices": session["alternative_matrices"],
            "ranked_alternatives": ranked_alternatives,
            "CR": CR
        })

        return render_template("result.html", result=result)

    except Exception as e:
        return render_template("result.html", error=f"Lỗi: {e}")

@result_bp.route("/export_excel")
def export_excel():
    try:
        criteria_weights = session.get("criteria_weights")
        ranked_alternatives = session.get("ranked_alternatives")

        if not criteria_weights or not ranked_alternatives:
            return redirect(url_for("result.result"))

        # Tạo DataFrame cho trọng số tiêu chí
        criteria_df = pd.DataFrame({
            "Tiêu chí": session["criteria_names"],
            "Trọng số": criteria_weights
        })

        # Tạo DataFrame cho xếp hạng phương án
        alternatives_df = pd.DataFrame(ranked_alternatives, columns=["Phương án", "Điểm"])

        # Ghi vào file Excel
        filepath = "output.xlsx"
        with pd.ExcelWriter(filepath) as writer:
            criteria_df.to_excel(writer, sheet_name="Trọng số tiêu chí", index=False)
            alternatives_df.to_excel(writer, sheet_name="Xếp hạng phương án", index=False)

        return send_file(filepath, as_attachment=True)
    except Exception as e:
        return render_template("result.html", error=f"Lỗi khi xuất file Excel: {e}")

@result_bp.route("/export_pdf")
def export_pdf():
    try:
        criteria_weights = session.get("criteria_weights")
        ranked_alternatives = session.get("ranked_alternatives")
        criteria_names = session.get("criteria_names")
        if not criteria_weights or not ranked_alternatives:
            return redirect(url_for("result.result"))

        # Vẽ biểu đồ tròn bằng matplotlib
        fig, ax = plt.subplots(figsize=(4, 4))
        labels = [alt for alt, _ in ranked_alternatives]
        sizes = [score for _, score in ranked_alternatives]
        colors_list = ['#0D706E', '#F9A825', '#43A047', '#E53935', '#3949AB', '#8E24AA', '#00838F', '#F4511E', '#6D4C41', '#757575']
        ax.pie(sizes, labels=labels, autopct='%1.2f%%', colors=colors_list[:len(labels)], startangle=90)
        ax.axis('equal')
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', bbox_inches='tight')
        plt.close(fig)
        img_buf.seek(0)

        # Tạo PDF
        pdf_buf = io.BytesIO()
        c = canvas.Canvas(pdf_buf, pagesize=A4)
        width, height = A4
        styles = getSampleStyleSheet()
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height-50, "Kết quả AHP")
        c.setFont("Helvetica", 12)

        # Bảng trọng số tiêu chí
        data_criteria = [["Tiêu chí", "Trọng số"]]
        for i in range(len(criteria_names)):
            data_criteria.append([criteria_names[i], f"{criteria_weights[i]:.4f}"])
        table_criteria = Table(data_criteria, hAlign='CENTER')
        table_criteria.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0D706E")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        table_criteria.wrapOn(c, width, height)
        table_criteria.drawOn(c, 60, height-150)

        # Bảng xếp hạng phương án
        data_alt = [["Phương án", "Điểm"]]
        for alt, score in ranked_alternatives:
            data_alt.append([alt, f"{score:.4f}"])
        table_alt = Table(data_alt, hAlign='CENTER')
        table_alt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0D706E")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        table_alt.wrapOn(c, width, height)
        table_alt.drawOn(c, 60, height-300)

        # Chèn biểu đồ tròn
        c.drawString(60, height-350, "Biểu đồ tỉ lệ xếp hạng phương án:")
        c.drawImage(img_buf, 180, height-500, width=200, height=200)

        c.save()
        pdf_buf.seek(0)
        pdf_path = os.path.abspath("ahp_result.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_buf.getbuffer())
        return send_file(pdf_path, as_attachment=True, download_name="ahp_result.pdf", mimetype='application/pdf')
    except Exception as e:
        return render_template("result.html", error=f"Lỗi khi xuất PDF: {e}")