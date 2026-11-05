# Sổ cái Quyết định Kiến trúc (Architecture Decisions Log)

Tài liệu này theo dõi trạng thái của **10 quyết định cốt lõi** (từ Mục 15 của [`03_OpenDash_CMS_PROPOSAL.md`](../03_OpenDash_CMS_PROPOSAL.md)) cùng các hợp đồng M0.

**Quy ước trạng thái:**
* `IN_DISCUSSION`: Đang thảo luận giữa Antigravity và Codex.
* `AGREED`: Cả hai AI đã thống nhất phương án kỹ thuật.
* `NEEDS_HUMAN`: Có từ 2 phương án khả thi trở lên liên quan đến định hướng sản phẩm, cần Chủ dự án chốt.

---

## Bảng Theo dõi Quyết định (M0 & Core Architecture)

| Mã | Hạng mục | Trạng thái | Phương án đang đề xuất / Đã chốt | Thread tham chiếu |
| :--- | :--- | :--- | :--- | :--- |
| **D01** | **SQLite Driver & Concurrency** | `IN_DISCUSSION` | Đề xuất so sánh `sqlx` vs `rusqlite` (1 writer + N readers pool) cho workload embedded single-binary. | [`01-m0-contracts-and-decisions.md`](./threads/01-m0-contracts-and-decisions.md) |
| **D02** | **Content Fields Schema (Hợp đồng 1)** | `IN_DISCUSSION` | Typed schema gắn theo CPT (`fields_schema`), chuẩn hóa JSON types + whitelist expression index. | [`01-m0-contracts-and-decisions.md`](./threads/01-m0-contracts-and-decisions.md) |
| **D03** | **AST Format & Bindings (Hợp đồng 2)** | `IN_DISCUSSION` | Namespace block (`core/*`, `theme/*`), tách `props`, `bindings`, `styles` (responsive), `children`. | [`01-m0-contracts-and-decisions.md`](./threads/01-m0-contracts-and-decisions.md) |
| **D04** | **Block Registry & Schema dùng chung** | `IN_DISCUSSION` | Open Registry nạp core blocks + theme blocks; chung JSON descriptor cho cả Rust validator và React OptionsPanel. | [`01-m0-contracts-and-decisions.md`](./threads/01-m0-contracts-and-decisions.md) |
| **D05** | **Compile-on-Save & Render Artifacts (Hợp đồng 3)** | `IN_DISCUSSION` | Cần chốt giữa *Compiled MiniJinja Template* vs *Segmented Render Plan JSON* cho trang có binding/query. | [`01-m0-contracts-and-decisions.md`](./threads/01-m0-contracts-and-decisions.md) |
| **D06** | **Draft, Revision & Publish Concurrency** | `IN_DISCUSSION` | Tách bảng `entry_revisions`, con trỏ `published_revision_id` / `draft_revision_id`, optimistic locking qua `version`. | [`01-m0-contracts-and-decisions.md`](./threads/01-m0-contracts-and-decisions.md) |
| **D07** | **Theme Ownership & Override** | `IN_DISCUSSION` | CPT/Fields thuộc site; Templates/Layouts gắn `theme_id`; gỡ/đổi theme không mất dữ liệu nội dung. | [`01-m0-contracts-and-decisions.md`](./threads/01-m0-contracts-and-decisions.md) |
| **D08** | **CSS Pipeline (`encre-css` vs CSS Vars)** | `IN_DISCUSSION` | Kết hợp CSS Variables/Scoped CSS cho dynamic props của Builder + `encre-css` cho utility classes trong template. | [`01-m0-contracts-and-decisions.md`](./threads/01-m0-contracts-and-decisions.md) |
| **D09** | **Cache & Dependency Tracking** | `IN_DISCUSSION` | Ghi `render_dependencies` ngay từ M2/M4; MVP invalidate theo generation counter + dependency scope. | [`01-m0-contracts-and-decisions.md`](./threads/01-m0-contracts-and-decisions.md) |
| **D10** | **Hook Contracts & QuickJS** | `IN_DISCUSSION` | Định nghĩa Rust trait/hook points ở M1–M2; hoãn nhúng `rquickjs` sang M6 sau khi CMS core hoàn chỉnh. | [`01-m0-contracts-and-decisions.md`](./threads/01-m0-contracts-and-decisions.md) |
