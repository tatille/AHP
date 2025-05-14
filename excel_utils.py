import pandas as pd
from datetime import datetime
import numpy as np

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
    Import dữ liệu từ file Excel
    """
    try:
        # Đọc các sheet
        criteria_df = pd.read_excel(file, sheet_name='Criteria Weights')
        alternatives_df = pd.read_excel(file, sheet_name='Alternative Weights')
        
        # Xử lý dữ liệu
        criteria = criteria_df['Criteria'].tolist()
        criteria_weights = criteria_df['Weight'].tolist()
        
        alternatives = alternatives_df['Alternative'].tolist()
        alternative_weights = alternatives_df.iloc[:, 1:].values.tolist()
        
        return {
            'criteria': criteria,
            'criteria_weights': criteria_weights,
            'alternatives': alternatives,
            'alternative_weights': alternative_weights
        }
    except Exception as e:
        raise ValueError(f"Lỗi khi đọc file Excel: {str(e)}") 