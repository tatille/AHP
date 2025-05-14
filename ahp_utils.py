import numpy as np

RI_TABLE = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
    11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59
}

def calculate_weights(matrix):
    try:
        # Đảm bảo matrix là NumPy array
        matrix = np.array(matrix, dtype=float)
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Ma trận phải là ma trận vuông.")

        # Kiểm tra giá trị hợp lệ trong ma trận
        if not np.all(np.isfinite(matrix)):
            raise ValueError("Ma trận chứa giá trị không hợp lệ (NaN hoặc Infinity).")

        # Kiểm tra tính đối xứng
        if not np.allclose(matrix, 1 / matrix.T, atol=1e-8):
            raise ValueError("Ma trận không đối xứng hợp lệ.")

        # Tính tổng cột
        col_sum = matrix.sum(axis=0)

        # Chuẩn hóa ma trận
        normalized_matrix = matrix / col_sum

        # Tính trọng số
        weights = normalized_matrix.mean(axis=1)

        # Tính chỉ số nhất quán (CR)
        lam_max = np.sum(np.dot(matrix, weights) / weights) / len(weights)
        CI = (lam_max - len(weights)) / (len(weights) - 1)
        RI = RI_TABLE.get(len(weights), None)
        if RI is None:
            raise ValueError(f"Không hỗ trợ ma trận kích thước {len(weights)}.")
        CR = CI / RI if RI else 0

        return weights, CR
    except Exception as e:
        raise ValueError(f"Lỗi khi tính toán trọng số: {e}")
