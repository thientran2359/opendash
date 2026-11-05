# OpenDash

CMS cho blog và website giới thiệu, dành cho người dùng quen WordPress. Rust, SQLite, một file thực thi cho mỗi bản cài và hệ theme/plugin riêng.

**Hiện trạng:** Chủ dự án đã xác nhận yêu cầu bản đầu. Phát triển trước trên Windows. Lát cắt Rust đầu tiên chạy luồng theme ZIP, preview và lưu một block vào SQLite.

## Bắt đầu ở đâu

1. Đọc [yêu cầu sản phẩm bản đầu](docs/05_PRODUCT_REQUIREMENTS_V1.md) để biết phạm vi đã được chủ dự án xác nhận.
2. Đọc [sổ thảo luận kỹ thuật](docs/discussions/DECISIONS_LOG.md) để tra các phương án D01–D10 từng được đề xuất.
3. Khi làm việc bằng AI, đọc [AGENTS.md](AGENTS.md) và [giao thức thảo luận](docs/discussions/PROTOCOL.md). Antigravity cần được yêu cầu đọc các file này; không giả định mọi công cụ tự nạp chúng.

## Bộ tài liệu

| Tài liệu | Vai trò |
|---|---|
| [05 — Yêu cầu sản phẩm bản đầu](docs/05_PRODUCT_REQUIREMENTS_V1.md) | Nguồn chính cho đánh giá tech stack |
| [06 — Đánh giá tech stack V1](docs/06_V1_TECH_STACK_EVALUATION.md) | Đề xuất stack, kết quả bản thử và phần cần kiểm chứng |
| [04 — Thiết kế và kế hoạch M0](docs/04_M0_DESIGN_AND_DELIVERY_PLAN.md) | Bản nháp tham khảo trước khi chốt yêu cầu |
| [03 — Đề xuất CMS-first](docs/03_OpenDash_CMS_PROPOSAL.md) | Lý do, ranh giới module và lộ trình M0–M6; chi tiết có thể được điều chỉnh bởi quyết định mới |
| [01 — Thiết kế gốc](docs/01_OpenDash_ARCHITECTURE_V2_ORIGINAL.md) | Lịch sử yêu cầu và tầm nhìn; SQL/SLA cũ không phải đặc tả production |
| [02 — Phân tích Daypress](docs/02_DAYPRESS_TECHNICAL_ANALYSIS.md) | Tham khảo có phân biệt mô tả gốc và kết quả đối chiếu; chưa phải bằng chứng OpenDash hoạt động |
| [Thread 01](docs/discussions/threads/01-m0-contracts-and-decisions.md) | Lịch sử trao đổi Antigravity ↔ Codex, chỉ nối tiếp các lượt |

Khi có khác biệt, ưu tiên chỉ đạo mới nhất của chủ dự án và yêu cầu đã xác nhận trong tài liệu 05. Kiến trúc và lộ trình cũ cần được đối chiếu lại với phạm vi mới.

## Chạy trên Windows

Từ thư mục repo, dùng Rust MSVC và Visual Studio Build Tools:

```powershell
cargo build --locked
python scripts/windows_smoke.py
python scripts/windows_smoke.py --theme "$env:TEMP\opendash-v1-theme.zip"
cargo run --locked
```

Mở [builder cục bộ](http://127.0.0.1:18766/builder), chọn gói ZIP mẫu, điền Tiêu đề và Mô tả, rồi thử Xem trước và Lưu. Dữ liệu nằm trong `data/opendash.sqlite`. Có thể đặt `OPENDASH_PORT` hoặc `OPENDASH_DB_PATH` cho lần chạy riêng.

Lát cắt dùng Axum, SQLx với SQLite nhúng và MiniJinja. File thực thi nhúng giao diện thử và migration, chỉ lắng nghe ở địa chỉ loopback. Phạm vi gồm một block trên trang chủ với các field văn bản. Cây bố cục, cập nhật theme, phân quyền và logic server của plugin thuộc các bước tiếp theo.

Dùng [bản thử cục bộ](spikes/stack-v1/README.md) để chạy lại các thử nghiệm runtime plugin. Kiểm tra file thực thi Linux sẽ thực hiện trước khi phát hành bản cho VPS.
