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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Đảm bảo Matplotlib sử dụng backend không phải GUI
import matplotlib
matplotlib.use('Agg')

# Đăng ký font hỗ trợ tiếng Việt (ví dụ: Arial)
# Đường dẫn có thể cần điều chỉnh tùy theo hệ điều hành và vị trí font
# Trên Windows, font Arial thường ở C:\Windows\Fonts\arial.ttf
try:
    pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:\\Windows\\Fonts\\arialbd.ttf'))
except Exception as e:
    print(f"Không thể đăng ký font Arial: {e}")

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
        criteria_matrix = [[
            float(Fraction(value)) if isinstance(value, str) and '/' in value else float(value)
            for value in row] for row in criteria_matrix
        ]

        alternative_matrices = [
            [
                [float(Fraction(value)) if isinstance(value, str) and '/' in value else float(value)
                 for value in row] for row in matrix
            ] for matrix in alternative_matrices
        ]

        # Tính toán chi tiết cho ma trận tiêu chí
        criteria_details = calculate_details(criteria_matrix)
        # Chuyển ma trận gốc trong details sang dạng phân số chuỗi
        criteria_details['matrix_fraction_str'] = [[str(Fraction(float(val)).limit_denominator()) for val in row] for row in criteria_details['matrix']]

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
            # Chuyển ma trận gốc trong details sang dạng phân số chuỗi
            details['matrix_fraction_str'] = [[str(Fraction(float(val)).limit_denominator()) for val in row] for row in details['matrix']]
            alternatives_details.append({
                'name': session['criteria_names'][i],
                'details': details,
                'alternatives': session['alternatives']
            })

        # Lưu lại vào session để các route export dùng được
        session["criteria_weights"] = weights.tolist()
        session["ranked_alternatives"] = ranked_alternatives
        # Lưu cả ma trận gốc dưới dạng list of lists
        session["criteria_matrix"] = criteria_matrix
        session["alternative_matrices"] = alternative_matrices
        
        # Lưu thêm các chi tiết cần thiết cho export PDF/Excel
        # Chuyển đổi NumPy arrays trong details sang list trước khi lưu vào session
        criteria_details_serializable = {}
        for key, value in criteria_details.items():
            if isinstance(value, np.ndarray):
                criteria_details_serializable[key] = value.tolist()
            else:
                criteria_details_serializable[key] = value

        alternatives_details_serializable = []
        for alt_detail in alternatives_details:
            alt_detail_serializable = {}
            for key, value in alt_detail.items():
                if key == 'details':
                    details_serializable = {}
                    for detail_key, detail_value in value.items():
                        if isinstance(detail_value, np.ndarray):
                            details_serializable[detail_key] = detail_value.tolist()
                        else:
                            details_serializable[detail_key] = detail_value
                    alt_detail_serializable[key] = details_serializable
                else:
                    alt_detail_serializable[key] = value
            alternatives_details_serializable.append(alt_detail_serializable)

        session["criteria_details"] = criteria_details_serializable
        session["alternatives_details"] = alternatives_details_serializable
        session["CR"] = CR
        session["criteria_names"] = session["criteria_names"]
        session["alternatives"] = session["alternatives"]

        # Chuẩn bị kết quả
        result = {
            "CR": CR,
            "weights": {session["criteria_names"][i]: weights[i] for i in range(len(weights))},
            "alternative_weights": alternative_weights,
            "ranked_alternatives": ranked_alternatives,
            "criteria_details": criteria_details_serializable,
            "criteria_names": session["criteria_names"],
            "alternatives": session["alternatives"],
            "alternatives_details": alternatives_details_serializable
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
        criteria_names = session.get("criteria_names")
        alternatives = session.get("alternatives")
        alternative_weights = session.get("alternative_weights")
        criteria_matrix = session.get("criteria_matrix")
        alternative_matrices = session.get("alternative_matrices")
        CR = session.get("CR")

        if not criteria_weights or not ranked_alternatives:
            return redirect(url_for("result.result"))

        # Tạo DataFrame cho trọng số tiêu chí
        criteria_df = pd.DataFrame({
            "Tiêu chí": criteria_names,
            "Trọng số": criteria_weights
        })

        # Tạo DataFrame cho xếp hạng phương án
        alternatives_df = pd.DataFrame(ranked_alternatives, columns=["Phương án", "Điểm"])

        # Tạo DataFrame cho ma trận so sánh cặp tiêu chí
        criteria_matrices_df = pd.DataFrame()
        if criteria_matrix:
            # Chuyển các giá trị float trong ma trận tiêu chí sang phân số dạng chuỗi
            criteria_matrix_fraction_str = [[str(Fraction(float(val)).limit_denominator()) for val in row] for row in criteria_matrix]
            
            matrix_df = pd.DataFrame(criteria_matrix_fraction_str, 
                                   index=criteria_names,
                                   columns=criteria_names)
            criteria_matrices_df = pd.concat([criteria_matrices_df, 
                                            pd.DataFrame({"Ma trận tiêu chí": [""]}),
                                            matrix_df,
                                            pd.DataFrame({"": [""]})], axis=0)

        # Tạo DataFrame cho ma trận so sánh cặp phương án theo từng tiêu chí
        alternative_matrices_dfs = []
        if alternative_matrices:
            for i, matrix in enumerate(alternative_matrices):
                if matrix:
                    # Chuyển các giá trị float trong ma trận phương án sang phân số dạng chuỗi
                    alternative_matrix_fraction_str = [[str(Fraction(float(val)).limit_denominator()) for val in row] for row in matrix]
                    
                    matrix_df = pd.DataFrame(alternative_matrix_fraction_str,
                                           index=alternatives,
                                           columns=alternatives)
                    # Thêm dòng tiêu đề cho từng ma trận phương án
                    header_df = pd.DataFrame({f"Ma trận phương án cho tiêu chí {criteria_names[i]}": [""]})
                    
                    alternative_matrices_dfs.append(header_df)
                    alternative_matrices_dfs.append(matrix_df)
                    alternative_matrices_dfs.append(pd.DataFrame({"": [""]}))

        # Ghi vào file Excel
        filepath = "output.xlsx"
        with pd.ExcelWriter(filepath) as writer:
            criteria_df.to_excel(writer, sheet_name="Trọng số tiêu chí", index=False)
            alternatives_df.to_excel(writer, sheet_name="Xếp hạng phương án", index=False)
            
            if not criteria_matrices_df.empty:
                 criteria_matrices_df.to_excel(writer, sheet_name="Ma trận tiêu chí", index=True)
            
            if alternative_matrices_dfs:
                 # Nối tất cả DataFrames ma trận phương án lại trước khi ghi
                 final_alternative_matrices_df = pd.concat(alternative_matrices_dfs, axis=0)
                 final_alternative_matrices_df.to_excel(
                    writer, sheet_name="Ma trận phương án", index=True)
            
            if CR is not None:
                 pd.DataFrame({
                    "Thông số": ["CR"],
                    "Giá trị": [CR]
                }).to_excel(writer, sheet_name="Thông số", index=False)

        return send_file(filepath, as_attachment=True)
    except Exception as e:
        import traceback
        print(f"Lỗi chi tiết khi xuất Excel: {str(e)}")
        print(f"Stack trace: {traceback.format_exc()}")
        return render_template("result.html", error=f"Lỗi khi xuất file Excel: {e}")

@result_bp.route("/export_pdf")
def export_pdf():
    try:
        # Lấy tất cả dữ liệu cần thiết từ session
        criteria_details = session.get("criteria_details")
        alternatives_details = session.get("alternatives_details")
        CR = session.get("CR")
        weights = session.get("criteria_weights")
        ranked_alternatives = session.get("ranked_alternatives")
        criteria_names = session.get("criteria_names")
        alternatives = session.get("alternatives")

        if not criteria_details or not alternatives_details or CR is None or not weights or not ranked_alternatives or not criteria_names or not alternatives:
             # Nếu thiếu dữ liệu, chuyển hướng về trang kết quả với thông báo lỗi
            return render_template("result.html", error="Không đủ dữ liệu để xuất PDF. Vui lòng chạy lại phân tích.")

        # Tạo PDF
        pdf_buf = io.BytesIO()
        c = canvas.Canvas(pdf_buf, pagesize=A4)
        width, height = A4
        styles = getSampleStyleSheet()
        
        # Khoảng cách lề
        margin = 40
        current_height = height - margin

        # Tiêu đề
        c.setFont("Arial-Bold", 18)
        c.drawCentredString(width/2, current_height, "Kết quả phân tích AHP")
        current_height -= 30
        
        # Chỉ số nhất quán (CR)
        c.setFont("Arial", 12)
        c.drawString(margin, current_height, f"Chỉ số nhất quán (CR): {CR:.4f}")
        current_height -= 30

        # Bảng trọng số tiêu chí
        c.setFont("Arial-Bold", 14)
        c.drawString(margin, current_height, "Trọng số tiêu chí:")
        current_height -= 20
        data_criteria_weights = [["Tiêu chí", "Trọng số"]]
        for i in range(len(criteria_names)):
            data_criteria_weights.append([criteria_names[i], f"{weights[i]:.4f}"])
        table_criteria_weights = Table(data_criteria_weights, hAlign='LEFT')
        table_criteria_weights.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0D706E")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Arial-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        w, h = table_criteria_weights.wrapOn(c, width, height)
        if current_height - h < margin:
            c.showPage()
            current_height = height - margin
        table_criteria_weights.drawOn(c, margin, current_height - h)
        current_height -= h + 20

        # Bảng chi tiết tính toán ma trận tiêu chí
        c.setFont("Arial-Bold", 14)
        c.drawString(margin, current_height, "Chi tiết tính toán ma trận tiêu chí:")
        current_height -= 20
        
        # Ma trận tiêu chí (dạng phân số)
        c.setFont("Arial", 10)
        if criteria_details and 'matrix_fraction_str' in criteria_details:
            data_criteria_matrix = [[""] + criteria_names]
            for i, row in enumerate(criteria_details['matrix_fraction_str']):
                data_criteria_matrix.append([criteria_names[i]] + row)
            table_criteria_matrix = Table(data_criteria_matrix, hAlign='LEFT')
            table_criteria_matrix.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#CCCCCC")),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTNAME', (0,0), (-1,-1), 'Arial'),
            ]))
            w, h = table_criteria_matrix.wrapOn(c, width - 2*margin, height)
            if current_height - h < margin:
                c.showPage()
                current_height = height - margin
            table_criteria_matrix.drawOn(c, margin, current_height - h)
            current_height -= h + 10

        # Các chi tiết tính toán khác của ma trận tiêu chí (Tổng cột, Ma trận chuẩn hóa,...) - Hiển thị dạng thập phân
        c.setFont("Arial", 10)
        details_to_show = [
            ("Tổng cột:", criteria_details.get('col_sum')), 
            ("Ma trận chuẩn hóa:", criteria_details.get('normalized_matrix')), 
            ("Trọng số (Criteria Weights):", criteria_details.get('weights')), 
            ("Weighted Sum:", criteria_details.get('weighted_sum')), 
            ("Consistency Vector:", criteria_details.get('consistency_vector'))
        ]
        
        for title, detail_data in details_to_show:
            if detail_data is not None:
                c.drawString(margin, current_height, title)
                current_height -= 15
                
                # Tạo bảng cho chi tiết tính toán
                data_detail = [[""] + (criteria_names if title != "Tổng cột:" else ["Tổng"]) ]
                if title == "Tổng cột:":
                     data_detail.append(["Tổng"] + [f'{v:.4f}' for v in detail_data])
                elif title == "Trọng số (Criteria Weights):":
                    data_detail = [[""] + criteria_names]
                    data_detail.append(["Trọng số"] + [f'{v:.4f}' for v in detail_data])
                else:
                    for i, row in enumerate(detail_data):
                        if isinstance(row, (list, tuple)):
                            data_detail.append([criteria_names[i]] + [f'{v:.4f}' for v in row])
                        else:
                            data_detail.append([criteria_names[i], f'{row:.4f}'])
                        
                table_detail = Table(data_detail, hAlign='LEFT')
                table_detail.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#CCCCCC")),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('FONTNAME', (0,0), (-1,-1), 'Arial'),
                ]))
                w, h = table_detail.wrapOn(c, width - 2*margin, height)
                if current_height - h < margin:
                    c.showPage()
                    current_height = height - margin
                table_detail.drawOn(c, margin, current_height - h)
                current_height -= h + 10

        # Chỉ số Lambda_max, CI, CR
        c.setFont("Arial", 12)
        current_height -= 10
        if criteria_details and criteria_details.get('lam_max') is not None:
             c.drawString(margin, current_height, f"Lamda_max: {criteria_details['lam_max']:.4f}")
             current_height -= 15
        if criteria_details and criteria_details.get('CI') is not None:
             c.drawString(margin, current_height, f"Chỉ số nhất quán CI: {criteria_details['CI']:.4f}")
             current_height -= 15
        if criteria_details and criteria_details.get('CR') is not None:
             c.drawString(margin, current_height, f"Chỉ số nhất quán CR: {criteria_details['CR']:.4f}")
             current_height -= 30

        # Bảng xếp hạng phương án
        c.setFont("Arial-Bold", 14)
        c.drawString(margin, current_height, "Xếp hạng phương án:")
        current_height -= 20
        data_ranked_alternatives = [["Phương án", "Điểm"]]
        for alt, score in ranked_alternatives:
            data_ranked_alternatives.append([alt, f"{score:.4f}"])
        table_ranked_alternatives = Table(data_ranked_alternatives, hAlign='LEFT')
        table_ranked_alternatives.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0D706E")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Arial-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,1), (-1,-1), 'Arial'),
        ]))
        w, h = table_ranked_alternatives.wrapOn(c, width, height)
        if current_height - h < margin:
            c.showPage()
            current_height = height - margin
        table_ranked_alternatives.drawOn(c, margin, current_height - h)
        current_height -= h + 20

        # Biểu đồ tròn (chèn ảnh)
        c.setFont("Arial-Bold", 14)
        c.drawString(margin, current_height, "Biểu đồ tỉ lệ xếp hạng phương án:")
        current_height -= 10
        # Vẽ biểu đồ tròn bằng matplotlib
        fig, ax = plt.subplots(figsize=(4, 4))
        labels = [alt for alt, _ in ranked_alternatives]
        sizes = [score for _, score in ranked_alternatives]
        colors_list = ['#0D706E', '#F9A825', '#43A047', '#E53935', '#3949AB', '#8E24AA', '#00838F', '#F4511E', '#6D4C41', '#757575']
        ax.pie(sizes, labels=labels, autopct='%1.2f%%', colors=colors_list[:len(labels)], startangle=90)
        ax.axis('equal')
        
        # Lưu biểu đồ vào file tạm
        temp_img_path = "temp_pie_chart.png"
        plt.savefig(temp_img_path, format='png', bbox_inches='tight')
        plt.close(fig)
        
        # Chèn ảnh biểu đồ vào PDF
        img_width = 200
        img_height = 200
        if current_height - img_height < margin:
            c.showPage()
            current_height = height - margin
        c.drawImage(temp_img_path, margin, current_height - img_height, width=img_width, height=img_height)
        current_height -= img_height + 20

        # Xóa file ảnh tạm
        try:
            os.remove(temp_img_path)
        except:
            pass

        # Chi tiết từng ma trận phương án (bước 4)
        c.setFont("Arial-Bold", 14)
        c.drawString(margin, current_height, "Chi tiết ma trận phương án cho từng tiêu chí:")
        current_height -= 20
        
        for alt_detail in alternatives_details:
            c.setFont("Arial-Bold", 12)
            c.drawString(margin, current_height, f"Tiêu chí: {alt_detail['name']}")
            current_height -= 15
            
            # Ma trận phương án (dạng phân số)
            c.setFont("Arial", 10)
            if alt_detail['details'] and 'matrix_fraction_str' in alt_detail['details']:
                 data_alt_matrix = [[""] + alt_detail['alternatives']]
                 for i, row in enumerate(alt_detail['details']['matrix_fraction_str']):
                     data_alt_matrix.append([alt_detail['alternatives'][i]] + row)
                 table_alt_matrix = Table(data_alt_matrix, hAlign='LEFT')
                 table_alt_matrix.setStyle(TableStyle([
                     ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#CCCCCC")),
                     ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                     ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                     ('FONTNAME', (0,0), (-1,-1), 'Arial'),
                 ]))
                 w, h = table_alt_matrix.wrapOn(c, width - 2*margin, height)
                 if current_height - h < margin:
                     c.showPage()
                     current_height = height - margin
                 table_alt_matrix.drawOn(c, margin, current_height - h)
                 current_height -= h + 10

            # Các chi tiết tính toán khác của ma trận phương án (Tổng cột, Ma trận chuẩn hóa,...) - Hiển thị dạng thập phân
            c.setFont("Arial", 10)
            alt_details_to_show = [
                ("Tổng cột:", alt_detail['details'].get('col_sum')), 
                ("Ma trận chuẩn hóa:", alt_detail['details'].get('normalized_matrix')), 
                ("Trọng số (Alternative Weights):", alt_detail['details'].get('weights')), 
                ("Weighted Sum:", alt_detail['details'].get('weighted_sum')), 
                ("Consistency Vector:", alt_detail['details'].get('consistency_vector'))
            ]
            
            for title, detail_data in alt_details_to_show:
                if detail_data is not None:
                    c.drawString(margin, current_height, title)
                    current_height -= 15
                    
                    # Tạo bảng cho chi tiết tính toán
                    data_detail = [[""] + (alt_detail['alternatives'] if title != "Tổng cột:" else ["Tổng"]) ]
                    if title == "Tổng cột:":
                         data_detail.append(["Tổng"] + [f'{v:.4f}' for v in detail_data])
                    elif title == "Trọng số (Alternative Weights)":
                        data_detail = [[""] + alt_detail['alternatives']]
                        data_detail.append(["Trọng số"] + [f'{v:.4f}' for v in detail_data])
                    else:
                        for i, row in enumerate(detail_data):
                            if isinstance(row, (list, tuple)):
                                data_detail.append([alt_detail['alternatives'][i]] + [f'{v:.4f}' for v in row])
                            else:
                                data_detail.append([alt_detail['alternatives'][i], f'{row:.4f}'])
                            
                    table_detail = Table(data_detail, hAlign='LEFT')
                    table_detail.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#CCCCCC")),
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                        ('FONTNAME', (0,0), (-1,-1), 'Arial'),
                    ]))
                    w, h = table_detail.wrapOn(c, width - 2*margin, height)
                    if current_height - h < margin:
                        c.showPage()
                        current_height = height - margin
                    table_detail.drawOn(c, margin, current_height - h)
                    current_height -= h + 10
                    
            # Chỉ số Lambda_max, CI, CR cho phương án theo tiêu chí
            c.setFont("Arial", 10)
            current_height -= 5
            if alt_detail['details'] and alt_detail['details'].get('lam_max') is not None:
                 c.drawString(margin, current_height, f"Lamda_max: {alt_detail['details']['lam_max']:.4f}")
                 current_height -= 15
            if alt_detail['details'] and alt_detail['details'].get('CI') is not None:
                 c.drawString(margin, current_height, f"Chỉ số nhất quán CI: {alt_detail['details']['CI']:.4f}")
                 current_height -= 15
            if alt_detail['details'] and alt_detail['details'].get('CR') is not None:
                 c.drawString(margin, current_height, f"Chỉ số nhất quán CR: {alt_detail['details']['CR']:.4f}")
                 current_height -= 20

        c.save()
        pdf_path = os.path.abspath("ahp_result.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_buf.getbuffer())
        return send_file(pdf_path, as_attachment=True, download_name="ahp_result.pdf", mimetype='application/pdf')
    except Exception as e:
        import traceback
        print(f"Lỗi chi tiết khi xuất PDF: {str(e)}")
        print(f"Stack trace: {traceback.format_exc()}")
        return render_template("result.html", error=f"Lỗi khi xuất file PDF: {e}")