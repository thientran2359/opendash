# Giao thức Thảo luận Kỹ thuật: Antigravity ↔ Codex (Dự án OpenDash)

Thư mục `discussions/` là không gian làm việc chung để **Antigravity** và **Codex** trao đổi, phản biện và chốt đặc tả kỹ thuật cho dự án **OpenDash** dưới sự giám sát của Chủ dự án (`HUMAN`).

---

## 1. Tài liệu Nền tảng (Context)

Trước khi viết phản hồi mới, cả 2 AI cần nắm rõ 3 tài liệu gốc ở thư mục gốc của dự án:
1. [`../01_OpenDash_ARCHITECTURE_V2_ORIGINAL.md`](../01_OpenDash_ARCHITECTURE_V2_ORIGINAL.md) — Bản đặc tả gốc ban đầu (tầm nhìn tổng thể, UX Builder 1 cột trái 340px + Clean Iframe, Single Binary).
2. [`../02_DAYPRESS_TECHNICAL_ANALYSIS.md`](../02_DAYPRESS_TECHNICAL_ANALYSIS.md) — Phân tích Daypress và Phụ lục A đối chiếu thực tế mã nguồn.
3. [`../03_OpenDash_CMS_PROPOSAL.md`](../03_OpenDash_CMS_PROPOSAL.md) — Đề xuất kiến trúc CMS-first, 3 Hợp đồng lõi (M0) và 10 quyết định cần chốt.

---

## 2. Cấu trúc Thư mục `discussions/`

* [`PROTOCOL.md`](./PROTOCOL.md): Quy tắc giao tiếp và làm việc chung (file này).
* [`DECISIONS_LOG.md`](./DECISIONS_LOG.md): Sổ cái ghi lại các quyết định đã thống nhất (`AGREED`), đang thảo luận (`IN_DISCUSSION`), hoặc cần Chủ dự án quyết định (`NEEDS_HUMAN`).
* `threads/*.md`: Các luồng thảo luận theo chủ đề cụ thể.

---

## 3. Quy tắc Viết bài trong `threads/*.md`

1. **Không sửa lịch sử của đối phương (Append-Only Turns)**:
   * Tuyệt đối **không xóa hoặc sửa** nội dung các lượt (`## [Turn N] ...`) trước đó.
   * Mỗi lần phản hồi, ghi thêm một section mới ở **cuối file** theo định dạng:
     ```markdown
     ---

     ## [Turn N] <Tên AI: Antigravity | Codex> — <YYYY-MM-DD>
     ```
2. **Cập nhật Header Trạng thái ở đầu file Thread**:
   Sau khi viết xong lượt của mình, AI vừa viết phải cập nhật lại phần metadata trên đầu file thread:
   * `Trạng thái`: `OPEN` | `NEEDS_HUMAN_INPUT` | `CONSENSUS_REACHED`
   * `Lượt hiện tại`: Số turn vừa hoàn thành
   * `Lượt tiếp theo`: `CODEX` | `ANTIGRAVITY` | `HUMAN`
3. **Cập nhật `DECISIONS_LOG.md`**:
   * Khi một điểm trong thread đã được cả 2 bên đồng thuận, AI ở lượt chốt có trách nhiệm cập nhật trạng thái mục đó trong [`DECISIONS_LOG.md`](./DECISIONS_LOG.md) sang `AGREED` kèm tóm tắt ngắn gọn.
4. **Phong cách Thảo luận**:
   * Đi thẳng vào cấu trúc dữ liệu, schema, trade-off kỹ thuật và khả năng triển khai trong Rust/TypeScript.
   * Phân biệt rõ: **Đồng thuận (Agree)**, **Phản biện / Đề xuất sửa đổi (Counter-proposal)**, và **Câu hỏi cần chốt ở lượt tới (Open Questions)**.
   * Giữ phương châm **Pragmatic MVP (CMS-first)**: Đủ chặt chẽ để không phải đập đi xây lại ở M2–M6, nhưng tránh over-engineering làm chậm M0–M1.
