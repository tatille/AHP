# AHP (Analytical Hierarchy Process) Web Application

## Giới thiệu

Đây là một ứng dụng web đơn giản triển khai phương pháp Phân tích Thứ bậc (Analytical Hierarchy Process - AHP). Ứng dụng cho phép người dùng nhập các tiêu chí và phương án, sau đó nhập ma trận so sánh cặp để tính toán trọng số và xếp hạng các phương án dựa trên phương pháp AHP. Kết quả có thể được xem trên giao diện web và xuất ra file Excel hoặc PDF.

## Yêu cầu

Để chạy dự án này, bạn cần cài đặt:

*   Python 3.6+ (Khuyến khích sử dụng môi trường ảo)
*   pip (Trình quản lý gói của Python)

## Cài đặt

Thực hiện các bước sau để clone repository và cài đặt các thư viện cần thiết:

1.  **Clone Repository:**

    ```bash
    git clone <địa chỉ repository của bạn>
    cd <tên thư mục dự án>
    ```

    *(Thay `<địa chỉ repository của bạn>` bằng URL repository của bạn)*
    *(Thay `<tên thư mục dự án>` bằng tên thư mục bạn clone về)*

2.  **Tạo và kích hoạt môi trường ảo (Tuỳ chọn nhưng khuyến khích):**

    ```bash
    # Tạo môi trường ảo
    python -m venv venv

    # Kích hoạt môi trường ảo
    # Trên Windows
    .\venv\Scripts\activate

    # Trên macOS/Linux
    source venv/bin/activate
    ```

3.  **Cài đặt các thư viện từ requirements.txt:**

    ```bash
    pip install -r requirements.txt
    ```

    *(Lưu ý: Nếu file `requirements.txt` chưa tồn tại, bạn cần tạo nó bằng cách chạy `pip freeze > requirements.txt` sau khi cài đặt thủ công các thư viện cần thiết như Flask, pandas, numpy, openpyxl, reportlab, matplotlib, pymongo, etc.)*

## Chạy ứng dụng

Sau khi cài đặt, bạn có thể chạy ứng dụng Flask bằng lệnh:

```bash
python app.py
```

Ứng dụng sẽ chạy trên http://127.0.0.1:5000/. Mở trình duyệt và truy cập địa chỉ này để sử dụng ứng dụng.

## Cấu trúc dự án

```
.
├── app.py          # File chính chạy ứng dụng Flask
├── routes/
│   ├── __init__.py
│   ├── excel_utils.py # Chức năng liên quan đến Excel
│   ├── result.py      # Route xử lý kết quả và xuất file
│   ├── step1.py       # Route cho bước nhập số lượng
│   ├── step2.py       # Route cho bước nhập tên
│   ├── step3.py       # Route cho bước nhập ma trận tiêu chí
│   ├── step4.py       # Route cho bước nhập ma trận phương án
│   └── ...
├── templates/
│   ├── base.html
│   ├── history.html   # Template xem lịch sử
│   ├── result.html    # Template hiển thị kết quả
│   ├── step1.html     # Template bước 1
│   ├── step2.html     # Template bước 2
│   ├── step3.html     # Template bước 3
│   ├── step4.html     # Template bước 4
│   └── ...
├── static/
│   ├── css/
│   │   └── common.css # File CSS chung
│   └── js/
│       └── ...
├── uploads/        # Thư mục tạm lưu file Excel upload (cần tạo thủ công hoặc qua code)
├── requirements.txt  # Danh sách các thư viện Python cần thiết
└── README.md       # File mô tả dự án và hướng dẫn
```

## Liên hệ

Nếu có bất kỳ câu hỏi hoặc góp ý nào, vui lòng liên hệ [Nhan Văn Ánh 1050080169 /10DH_CNPM3 ]. 