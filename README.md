# OpenDash

CMS cho blog và website giới thiệu, dành cho người dùng quen WordPress. Rust, SQLite, một file thực thi cho mỗi bản cài và hệ theme/plugin riêng.

**Hiện trạng:** Chủ dự án đã xác nhận yêu cầu bản đầu. Tech stack chi tiết đang chờ đánh giá. Repository hiện chứa tài liệu dự án.

## Bắt đầu ở đâu

1. Đọc [yêu cầu sản phẩm bản đầu](docs/05_PRODUCT_REQUIREMENTS_V1.md) để biết phạm vi đã được chủ dự án xác nhận.
2. Đọc [sổ thảo luận kỹ thuật](docs/discussions/DECISIONS_LOG.md) để tra các phương án D01–D10 từng được đề xuất.
3. Khi làm việc bằng AI, đọc [AGENTS.md](AGENTS.md) và [giao thức thảo luận](docs/discussions/PROTOCOL.md). Antigravity cần được yêu cầu đọc các file này; không giả định mọi công cụ tự nạp chúng.

## Bộ tài liệu

| Tài liệu | Vai trò |
|---|---|
| [05 — Yêu cầu sản phẩm bản đầu](docs/05_PRODUCT_REQUIREMENTS_V1.md) | Nguồn chính cho đánh giá tech stack |
| [04 — Thiết kế và kế hoạch M0](docs/04_M0_DESIGN_AND_DELIVERY_PLAN.md) | Bản nháp tham khảo trước khi chốt yêu cầu |
| [03 — Đề xuất CMS-first](docs/03_OpenDash_CMS_PROPOSAL.md) | Lý do, ranh giới module và lộ trình M0–M6; chi tiết có thể được điều chỉnh bởi quyết định mới |
| [01 — Thiết kế gốc](docs/01_OpenDash_ARCHITECTURE_V2_ORIGINAL.md) | Lịch sử yêu cầu và tầm nhìn; SQL/SLA cũ không phải đặc tả production |
| [02 — Phân tích Daypress](docs/02_DAYPRESS_TECHNICAL_ANALYSIS.md) | Tham khảo có phân biệt mô tả gốc và kết quả đối chiếu; chưa phải bằng chứng OpenDash hoạt động |
| [Thread 01](docs/discussions/threads/01-m0-contracts-and-decisions.md) | Lịch sử trao đổi Antigravity ↔ Codex, chỉ nối tiếp các lượt |

Khi có khác biệt, ưu tiên chỉ đạo mới nhất của chủ dự án và yêu cầu đã xác nhận trong tài liệu 05. Kiến trúc và lộ trình cũ cần được đối chiếu lại với phạm vi mới.

## Bước tiếp theo

Đánh giá tech stack theo yêu cầu bản đầu, với trọng tâm là builder, theme/plugin ZIP, runtime plugin và cách đóng gói cài đặt. Xác định những giả định cần thử nghiệm trước khi chọn stack và viết kế hoạch triển khai.

Lệnh build/test sẽ được bổ sung khi workspace và công cụ thực sự tồn tại. Hiện chưa có lệnh `cargo test`, `npm test` hay server được xác nhận cho repository này.
