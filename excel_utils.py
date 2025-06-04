import pandas as pd
from datetime import datetime
import numpy as np
import os

def create_template_excel():
    """
    Tạo file Excel mẫu với cấu trúc chuẩn
    """
    try:
        print("Bắt đầu tạo template Excel...")
        
        # Tạo thư mục templates nếu chưa tồn tại
        template_dir = os.path.join('static', 'templates')
        print(f"Tạo thư mục: {template_dir}")
        os.makedirs(template_dir, exist_ok=True)
        
        # Đường dẫn đầy đủ đến file template
        template_path = os.path.join(template_dir, 'ahp_template.xlsx')
        print(f"Đường dẫn template: {template_path}")
        
        # Tạo DataFrame cho sheet Criteria
        print("Tạo DataFrame cho sheet Criteria...")
        criteria_data = {
            'Criteria': ['Tiêu chí 1', 'Tiêu chí 2', 'Tiêu chí 3'],
            'Tiêu chí 1': [1, 2, 3],
            'Tiêu chí 2': [1/2, 1, 2],
            'Tiêu chí 3': [1/3, 1/2, 1]
        }
        criteria_df = pd.DataFrame(criteria_data)
        print("DataFrame Criteria đã tạo xong")
        
        # Tạo ma trận so sánh cặp cho từng tiêu chí (ví dụ 3 phương án)
        print("Tạo ma trận so sánh cặp phương án mẫu...")
        alt_matrix_template = np.array([
            [1, 2, 3],
            [1/2, 1, 2],
            [1/3, 1/2, 1]
        ])
        
        # Lấy danh sách phương án mẫu
        alternatives_list = ['Phương án 1', 'Phương án 2', 'Phương án 3']

        # Tạo DataFrame cho sheet Alternatives
        print("Tạo DataFrame cho sheet Alternatives...")
        alternatives_data = {
            'Alternative': alternatives_list
        }
        
        # Thêm các ma trận so sánh cặp phương án vào dữ liệu cho mỗi tiêu chí
        num_criteria = len(criteria_data['Criteria'])
        for i in range(num_criteria):
            for j in range(len(alternatives_list)):
                col_name = f'Tiêu chí {i+1}.{alternatives_list[j]}' # Tên cột dạng 'Tiêu chí X.Phương án Y'
                alternatives_data[col_name] = alt_matrix_template[:, j].tolist()
            
        alternatives_df = pd.DataFrame(alternatives_data)
        print("DataFrame Alternatives đã tạo xong")
        
        # Ghi vào file Excel
        print("Bắt đầu ghi vào file Excel...")
        with pd.ExcelWriter(template_path, engine='openpyxl') as writer:
            print("Ghi sheet Criteria...")
            criteria_df.to_excel(writer, sheet_name='Criteria', index=False)
            
            print("Ghi sheet Alternatives...")
            alternatives_df.to_excel(writer, sheet_name='Alternatives', index=False)
            
            print("Ghi sheet Hướng dẫn...")
            guide_data = {
                'Hướng dẫn': [
                    '1. Sheet "Criteria":',
                    '   - Cột "Criteria": Tên các tiêu chí',
                    '   - Các cột còn lại: Ma trận so sánh cặp tiêu chí (NxN cột, N là số tiêu chí)',
                    '',
                    '2. Sheet "Alternatives":',
                    '   - Cột "Alternative": Tên các phương án',
                    '   - Các cột còn lại: Ma trận so sánh cặp phương án cho từng tiêu chí.',
                    '     Mỗi khối ma trận cho một tiêu chí gồm MxM cột (M là số phương án).'
                    '     Các cột trong khối ma trận cho "Tiêu chí X" nên đặt tên là "Tiêu chí X.Phương án Y".',
                    '',
                    'Lưu ý:',
                    '- Số lượng tiêu chí và phương án tối thiểu là 3',
                    '- Giá trị trong ma trận so sánh cặp phải tuân theo thang đo AHP (1-9)',
                    '- Giá trị nghịch đảo phải được nhập dưới dạng phân số (ví dụ: 1/2, 1/3, ...)'
                ]
            }
            pd.DataFrame(guide_data).to_excel(writer, sheet_name='Hướng dẫn', index=False)
            
        print("Đã ghi xong file Excel")
        
        # Kiểm tra file đã tạo
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Không tìm thấy file template tại {template_path}")
            
        print(f"Template đã được tạo thành công tại: {template_path}")
        return template_path
        
    except Exception as e:
        print(f"Lỗi chi tiết: {str(e)}")
        print(f"Loại lỗi: {type(e).__name__}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        raise Exception(f"Lỗi khi tạo template Excel: {str(e)}")

def export_to_excel(data, filename=None):
    """
    Xuất dữ liệu AHP ra file Excel
    """
    if filename is None:
        filename = f"ahp_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # Tạo DataFrame cho từng sheet
    criteria_df = pd.DataFrame(data['criteria_weights'], 
                             columns=['Criteria', 'Weight'])
    
    alternatives_df = pd.DataFrame(data['alternative_weights'],
                                 columns=['Alternative'] + data['criteria'])
    
    # Tạo Excel writer
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        criteria_df.to_excel(writer, sheet_name='Criteria Weights', index=False)
        alternatives_df.to_excel(writer, sheet_name='Alternative Weights', index=False)
        
        # Thêm sheet tổng hợp
        summary_df = pd.DataFrame({
            'Alternative': data['alternatives'],
            'Total Score': data['final_scores']
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    return filename

def import_from_excel(file):
    """
    Đọc dữ liệu từ file Excel
    """
    try:
        print(f"Bắt đầu nhập dữ liệu từ file: {file}")
        # Đọc các sheet từ file Excel
        print("Đọc sheet Criteria...")
        df_criteria = pd.read_excel(file, sheet_name='Criteria')
        print("Đọc sheet Alternatives...")
        df_alternatives = pd.read_excel(file, sheet_name='Alternatives')
        print("Đã đọc xong các sheet")
        
        # Kiểm tra dữ liệu tiêu chí
        print("Kiểm tra dữ liệu tiêu chí...")
        if df_criteria.empty:
            raise ValueError("Sheet Criteria không có dữ liệu")
            
        # Lấy danh sách tiêu chí
        criteria = df_criteria['Criteria'].tolist()
        print(f"Danh sách tiêu chí: {criteria}")
        if len(criteria) < 3:
            raise ValueError("Cần ít nhất 3 tiêu chí")
            
        # Kiểm tra dữ liệu phương án
        print("Kiểm tra dữ liệu phương án...")
        if df_alternatives.empty:
            raise ValueError("Sheet Alternatives không có dữ liệu")
            
        # Lấy danh sách phương án
        alternatives = df_alternatives['Alternative'].tolist()
        print(f"Danh sách phương án: {alternatives}")
        if len(alternatives) < 3:
            raise ValueError("Cần ít nhất 3 phương án")
            
        # Lấy ma trận so sánh cặp tiêu chí
        print("Lấy ma trận so sánh cặp tiêu chí...")
        criteria_matrix = df_criteria.iloc[:, 1:len(criteria)+1].values
        print(f"Ma trận tiêu chí:\n{criteria_matrix}")
        
        # Kiểm tra kích thước ma trận tiêu chí
        if criteria_matrix.shape != (len(criteria), len(criteria)):
            raise ValueError("Ma trận so sánh cặp tiêu chí không đúng kích thước")
            
        # Lấy ma trận so sánh cặp phương án cho từng tiêu chí
        print("Lấy ma trận so sánh cặp phương án...")
        alternative_matrices = []
        for i in range(len(criteria)):
            # Kiểm tra cột tồn tại trước khi truy cập
            col_start = i * len(alternatives) + 1
            col_end = col_start + len(alternatives)
            if col_end > df_alternatives.shape[1]:
                 raise ValueError(f"Thiếu cột ma trận phương án cho tiêu chí {criteria[i]}")
            matrix = df_alternatives.iloc[:, col_start:col_end].values
            if matrix.shape != (len(alternatives), len(alternatives)):
                raise ValueError(f"Ma trận so sánh cặp phương án cho tiêu chí {criteria[i]} không đúng kích thước")
            alternative_matrices.append(matrix)
            print(f"Ma trận phương án cho tiêu chí {criteria[i]}:\n{matrix}")
            
        # Tính toán trọng số tiêu chí
        print("Tính toán trọng số tiêu chí...")
        eigenvalues, eigenvectors = np.linalg.eig(criteria_matrix)
        max_index = np.argmax(eigenvalues.real)
        weights = eigenvectors[:, max_index].real
        weights = weights / np.sum(weights)
        print(f"Trọng số tiêu chí: {weights.tolist()}")
        
        # Tính toán trọng số phương án cho từng tiêu chí
        print("Tính toán trọng số phương án...")
        alternative_weights = {}
        for i, matrix in enumerate(alternative_matrices):
            eigenvalues, eigenvectors = np.linalg.eig(matrix)
            max_index = np.argmax(eigenvalues.real)
            weight = eigenvectors[:, max_index].real
            weight = weight / np.sum(weight)
            alternative_weights[criteria[i]] = weight.tolist()
            print(f"Trọng số phương án cho tiêu chí {criteria[i]}: {weight.tolist()}")
            
        print("Nhập dữ liệu thành công.")
        return {
            'criteria': criteria,
            'criteria_weights': weights.tolist(),
            'alternatives': alternatives,
            'alternative_weights': alternative_weights,
            'criteria_matrix': criteria_matrix.tolist(),
            'alternative_matrices': [m.tolist() for m in alternative_matrices]
        }
    except Exception as e:
        print(f"Lỗi trong import_from_excel: {str(e)}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        raise ValueError(f"Lỗi khi đọc file Excel: {str(e)}") 