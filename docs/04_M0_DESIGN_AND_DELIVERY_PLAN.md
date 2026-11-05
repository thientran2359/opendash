# OpenDash — Kết quả thiết kế và kế hoạch M0

> **Bản nháp tham khảo, chưa được chủ dự án duyệt.** Dùng [yêu cầu sản phẩm bản đầu](05_PRODUCT_REQUIREMENTS_V1.md) cho phạm vi hiện hành. Các giả định bên dưới về nháp/xuất bản, revisions, plugin runtime và kế hoạch M0 cần đánh giá lại.

Ngày: 2026-11-06. Nguồn trao đổi: [Thread 01](discussions/threads/01-m0-contracts-and-decisions.md), [D01–D10](discussions/DECISIONS_LOG.md). Phạm vi phiên làm việc: thảo luận và hoàn thiện hướng tài liệu, chưa viết runtime hay push thay đổi.

**Trạng thái:** hai AI đồng thuận thiết kế D01–D10 qua Turn 1–3; M0 chưa nghiệm thu. Các contract/fixtures/spike và slice đầu chưa triển khai. Turn 4–5 dành cho rà soát bản tổng hợp và giới hạn của đồng thuận.

## 1. Kết quả cần đạt

Xây CMS dùng được trước: quản lý nội dung có kiểu, draft/revision, theme mở, visual builder với sidebar trái 340px và iframe thật. Một executable trên production; data/uploads/themes vẫn là trạng thái riêng. Chưa làm e-commerce, QuickJS hay self-update.

Ba hợp đồng M0 phải mô tả được cùng một trang: hero tĩnh, heading lấy title, collection có lọc/phân trang, và symbol dùng lặp hai lần. Tên format trong tài liệu này là hướng thiết kế; schema chuẩn và fixture đầy đủ vẫn là đầu ra tiếp theo, chưa có runtime xác minh chúng.

## 2. Hướng kỹ thuật

| Nhóm | Kết luận thiết kế | Điều phải kiểm chứng |
|---|---|---|
| Storage | sqlx + SQLite WAL; một writer, read pool bounded khởi điểm 2; synchronous FULL mặc định | Cấu hình từng connection, conflict, reopen/rollback, chi phí bộ nhớ; NORMAL chỉ là cấu hình có tradeoff |
| Content | Typed fields theo CPT, schema version; content model thuộc site | Missing/null/default, giới hạn số/date, schema migration, bound queries và query plan |
| Public data | Revisions bất biến + published_entries projection | Sửa draft không đổi public HTML, route hoặc collection filter/sort |
| AST/registry | ast_version ở document; block_version ở node; namespace, props/bindings/styles/children; descriptor chung | Constraints, migration, missing block, IDs, hai instance cùng symbol |
| Artifacts | static_html hoặc minijinja_v1; data tách template source; async query prefetch | Text chứa cú pháp template không bị thực thi; output escaping, deterministic dependencies |
| Preview | Một root cho mỗi renderable block, HTML parser/API có cấu trúc; CSS/assets manager riêng | Morph trong table/list context, response cũ, auth/origin/source, asset lifecycle |
| CSS | CSS variables/scoped CSS cho Builder; CSS theme viết sẵn được hỗ trợ | Preview/publish cùng output; whitelist values; encre-css là spike tùy chọn |
| Publish/cache | Atomic pointer + projection + artifact/dependencies + generation; invalidate rộng trước | Compile lỗi/conflict không hỏng public; render cũ không vào generation mới |
| Extensions | Hook contract sớm; Rust handlers trước; QuickJS sau | Payload/order/error/cache policy có version trước khi mở runtime plugin |

Các con số <50µs, <1ms, <2ms, RAM 12–25MB trong thiết kế gốc vẫn là mục tiêu chưa đo. Không dùng chúng làm bằng chứng hoàn thành.

## 3. Ba hợp đồng phải viết thành đầu ra cụ thể

### Content fields v1

Đầu ra dự kiến: `docs/contracts/content-fields-v1.md` và `docs/fixtures/content/`.

- Xác định key/ID ổn định, type, required, default, nullability, constraints, filter/sort operators và UI metadata.
- M0 bắt đầu bằng text, number, boolean, date, select và media ID; schema chỉ khai báo các type thực sự hỗ trợ. Relation/repeater/gallery/rich text bổ sung tuần tự với validation riêng.
- Field label đổi tự do; key/type đổi phải có migration policy, schema version và tác động đến projections/artifacts/bindings.
- `json_extract` giữ kiểu scalar JSON đã validate, tránh CAST chuỗi lỗi thành số 0. Quy định missing/null/sort null và miền số trước khi index.
- Index là tối ưu có quản lý, không chạy DDL tùy ý theo mọi thao tác UI. Public index đặt trên public projection; `EXPLAIN QUERY PLAN` trên đúng query có bind.
- Taxonomy/relations dùng public phải gắn published revision hoặc projection tương ứng; không join ngược vào quan hệ draft có thể sửa. `published_entries` riêng lẻ không đủ nếu public dependencies còn mutable/draft. Các settings/media/menu sửa trực tiếp public cần lifecycle và invalidation được ghi rõ.

### AST và registry v1

Đầu ra dự kiến: `docs/contracts/ast-and-registry-v1.md` và `docs/fixtures/ast/`.

- Document có ast_version và root nodes; node có id, type, block_version, props, bindings, styles, children; label/hidden có semantics rõ.
- Descriptor dùng chung định nghĩa props, UI, binding targets/types, parent-child, renderer, assets, migration và cache behavior. Theme override renderer không âm thầm thay schema.
- Binding là cấu trúc dữ liệu được whitelist, không nhận code tùy ý; props tĩnh/fallback và binding có quy tắc ưu tiên xác định.
- Single root áp dụng cho output block, không tự bọc div khi vi phạm. Symbol-ref có instance path; không cho sửa children tại nơi dùng nếu chưa có override contract.
- Style/selection keys trong symbol phải bao gồm instance path nếu có output/override theo instance; `node_id` đơn lẻ không bảo đảm duy nhất. Chọn HTML parser theo spike fragment-context; parser/rewriter không mặc nhiên sanitize HTML.
- Public không có data-ux-*; class/data scope CSS public là định danh riêng. Preview metadata không làm đổi semantics layout.

### Render artifacts v1

Đầu ra dự kiến: `docs/contracts/render-artifacts-v1.md` và `docs/fixtures/render/`.

- Identity: source revision, artifact/compiler version, theme/registry revision, content schema version; kind; assets; dependency scopes.
- `static_html` là output cuối, không parse lại thành template. `minijinja_v1` chỉ parse trusted template/compiler source; props/user text/static chunks là context data, không nối trở lại source.
- Trusted HTML chỉ do renderer/sanitizer phía server tạo; không tin cờ safe từ client/JSON. HTML escaping không đủ cho URL/CSS/rich text.
- Queries có cấu trúc và giới hạn; Rust service prefetch, MiniJinja render không gọi DB/network. Collection item renderer là template đã parse/ref hợp lệ.
- Snapshot/publish transaction kiểm tra version và dependency versions trước commit. Files generated được stage/ghi nguyên tử trước khi DB trỏ tới; lỗi/crash không để public tham chiếu file chưa tồn tại. Orphan files có thể dọn sau.
- Revision pointers dùng composite FK tới `(entry_id, revision_id)` tương ứng với UNIQUE key ở bảng revisions; deferred constraints cần fixture commit/rollback và vòng đời delete/restore. SQL minh họa trong thread chưa phải migration đã chạy.
- Đọc generation + entry + collections trong một read transaction bounded, kết thúc trước render/compression chậm; không kéo dài snapshot vì có thể cản checkpoint. `BEGIN DEFERRED` chọn thời điểm transaction, không tự biến writable connection thành read-only. Kết quả mutation lấy từ snapshot trong transaction, không SELECT lại sau commit rồi coi chắc chắn là kết quả của chính mutation đó.
- Artifact stale phải rebuild hoặc dùng last-good output theo policy có ghi rõ; cache clear không thay thế rebuild.

Các đường dẫn contracts/fixtures ở trên là **đầu ra cần tạo**, hiện chưa có; không coi chúng là schema đã tồn tại.

## 4. Trình tự làm code

| Bước | Đầu ra | Nghiệm thu trước khi mở rộng |
|---|---|---|
| M0-A | Ba contract + fixtures positive/negative + dependency/API versions chọn cho spike | Cùng fixture trang được editor/server mô tả nhất quán; nêu rõ version/migration |
| M0-B | Spike compiler MiniJinja và CSS/root handling nhỏ | User text chứa {{...}}/{%...%} giữ là data; static/binding/query hoạt động; root semantics và CSS không lệch |
| M0-C | Spike SQLite publish/projection/generation | Draft không rò; conflict/failed compile/rollback; query plan; snapshot/generation nhất quán |
| Slice đầu | Cargo core/server và Admin tối thiểu, chỉ UI cần cho luồng thử | Tạo entry → sửa AST/draft → preview → publish → public → sửa draft lần nữa → public cũ giữ nguyên |
| M1–M2 | Hoàn thiện auth/content/media/menu/theme; xem proposal 03 | Revision restore, backup/restore, theme update/switch và last-good publish |
| M3–M6 | Builder đầy đủ, dynamic content, vận hành, sau cùng plugins | Mỗi mốc nghiệm thu riêng theo proposal, không mở rộng đồng loạt |

Không dựng toàn Admin, commerce tables hoặc nhiều crate trước khi slice đầu cho thấy ranh giới cần thiết. Ban đầu core độc lập HTTP/SQLite, server sở hữu routes/services/storage, Admin React/TypeScript. Dependency versions và lệnh build/test ghi sau khi chọn và chạy thực tế.

## 5. Các kịch bản nghiệm thu có giá trị

1. Publish A → sửa draft B: public entry, title, route và collection vẫn là A; publish B đổi đồng bộ.
2. Hai tab cùng version: chỉ một mutation được chấp nhận; tab cũ nhận conflict; dữ liệu công khai không bị overwrite.
3. Compile/migration/publish lỗi: transaction rollback, bản public trước và assets vẫn dùng được.
4. Text chứa `{{ 7 * 7 }}`, `{% ... %}`, HTML, dấu quote, URL/CSS không hợp lệ: không thực thi template/XSS; hành vi allow/reject được ghi theo type/context.
5. Một symbol xuất hiện hai lần; không duplicate DOM selection key; vòng symbol bị từ chối; thay symbol public không kéo draft vào trang.
6. Response preview out-of-order bị bỏ; thêm block nạp đủ assets; fragment vẫn đúng root context; public không có metadata editor.
7. Cache render đồng thời publish/unpublish: kết quả generation cũ không ghi vào namespace mới; collection mới/xóa/đổi sort được phản ánh đúng.
8. Theme/registry/schema đổi: stale artifacts được xử lý theo policy, không mất source; backup restore sang thư mục mới được.

Đây là tiêu chí sẽ chạy khi có code, **không phải báo cáo tests đã pass**.

## 6. Skill và plugin

**Nên làm ngay:** README + AGENTS.md + decision log + contracts/fixtures + acceptance checks. Đây là phần giữ hai AI cùng nguồn quyết định.

**Skill tùy chỉnh đáng tạo sau khi thử workflow:** `opendash-contract-review` (đối chiếu contract/schema/fixture/compatibility) và `opendash-vertical-slice` (thực hiện use case, kiểm chứng rủi ro, cập nhật bằng chứng). Chưa tạo/cài trong phiên này; trước mắt quy tắc repo đủ để bắt đầu. Skill nên nhỏ, có trigger và đầu ra cụ thể; không nhồi lại toàn kiến trúc vào mỗi skill.

**Plugin ưu tiên duy nhất:** Context7 để tra tài liệu API theo thư viện/phiên bản. Sau đề xuất, plugin đã có công cụ trong phiên và gọi thành công resolve/query MiniJinja (`/mitsuhiko/minijinja`, ví dụ từ repository upstream). Chưa pin dependency hoặc xác minh coverage cho toàn stack; thư viện không có thì dùng tài liệu chính thức. GitHub/browser đã có công cụ; chưa cần Notion, Linear hay plugin AI-to-AI. Tài liệu tiếp tục ở Markdown cùng repo để review diff và truy vết.

## 7. Nguồn

- Lý do và phản biện: [Thread 01](discussions/threads/01-m0-contracts-and-decisions.md), [proposal CMS-first](03_OpenDash_CMS_PROPOSAL.md).
- [MiniJinja API](https://docs.rs/minijinja/latest/minijinja/), [sqlx SQLite options](https://docs.rs/sqlx/latest/sqlx/sqlite/struct.SqliteConnectOptions.html), [SQLite expression indexes](https://www.sqlite.org/expridx.html), [SQLite WAL](https://www.sqlite.org/wal.html), đọc 2026-11-06. Latest URLs là nguồn tra cứu, không phải phiên bản dependency đã pin.
- Bổ sung Turn 3–4: [SQLite JSON scalar extraction](https://www.sqlite.org/json1.html), [composite/deferred foreign keys](https://www.sqlite.org/foreignkeys.html). Chưa chạy SQL migration từ các ví dụ này.
- [OpenAI: AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [OpenAI: skills](https://developers.openai.com/plugins/concepts/skills): nguồn hướng dẫn tổ chức instructions/workflow; các lựa chọn cụ thể cho OpenDash trong tài liệu này là đề xuất của hai AI.
