# Evaluation Directory

Thư mục này chứa các công cụ đánh giá cho các thành phần khác nhau của dự án.

## 📁 Cấu trúc

- `rag_evaluator.py` - Đánh giá hệ thống RAG (Retrieval-Augmented Generation)
- `__init__.py` - Package initialization

## 🔄 Di chuyển LLM Evaluation

**⚠️ THÔNG BÁO QUAN TRỌNG:**

Các công cụ đánh giá mô hình LLM (như VMLU evaluation) đã được di chuyển ra thư mục riêng:

```
📁 llm-evaluation/          # ← Vị trí mới
├── vmlu_evaluator.py       # Đánh giá VMLU
├── download_vmlu.py        # Tải dataset
├── check_dataset.py        # Kiểm tra dataset
├── run_vmlu_evaluation.sh  # Script tự động
├── requirements.txt        # Dependencies riêng
└── README.md              # Hướng dẫn chi tiết
```

## 🚀 Cách sử dụng LLM Evaluation

### Đánh giá mô hình jCool10/jCool10-LLaMA3-VietQA-3B-merged:

```bash
# Di chuyển tới thư mục llm-evaluation
cd ../llm-evaluation

# Cài đặt dependencies
pip install -r requirements.txt

# Kiểm tra dataset
python check_dataset.py

# Chạy evaluation
python vmlu_evaluator.py --model jCool10/jCool10-LLaMA3-VietQA-3B-merged
```

### Hoặc sử dụng script tự động:

```bash
cd ../llm-evaluation
bash run_vmlu_evaluation.sh
```

## 📖 Tài liệu

Xem `llm-evaluation/README.md` để biết hướng dẫn chi tiết về:

- Cài đặt và cấu hình
- Các tùy chọn evaluation
- Format kết quả
- Troubleshooting

## 🔗 Liên quan

- **RAG Evaluation**: Sử dụng `rag_evaluator.py` trong thư mục này
- **LLM Evaluation**: Sử dụng tools trong `../llm-evaluation/`
