# OpenDash — TÀI LIỆU ĐẶC TẢ KIẾN TRÚC HỆ THỐNG

**Dự án:** OpenDash — Rust All-in-One CMS & E-commerce Engine  
**Kiến trúc:** Single-Binary, UX-Style Visual Builder (Sidebar Tree + Clean Iframe), Zero-Code CPT/Fields, Sandboxed JS Plugins  
**Phiên bản bản thiết kế gốc:** 2.0.0-UX  
**Ngày đóng gói tài liệu:** 2026-11-05  
**Trạng thái:** Bản thiết kế ban đầu do chủ dự án cung cấp; chưa phải đặc tả triển khai đã chốt.

> **Cách đọc bộ tài liệu**
>
> File này khôi phục nội dung bản đặc tả đầu tiên và chuẩn hóa tên dự án thành **OpenDash**. Các định danh `cms-*`, schema SQL, mục tiêu hiệu năng và phạm vi e-commerce được giữ để bảo toàn bản tham chiếu.
>
> Ưu tiên mới nhất của dự án là **xây CMS trước**. Các con số hiệu năng dưới đây là mục tiêu của bản gốc, chưa phải kết quả benchmark hoặc cam kết đã xác nhận. Các điều chỉnh về dữ liệu, renderer, plugin, backup và lộ trình nằm trong [03_OpenDash_CMS_PROPOSAL.md](03_OpenDash_CMS_PROPOSAL.md).
>
> Phân tích Daypress và các điểm đã đối chiếu nằm trong [02_DAYPRESS_TECHNICAL_ANALYSIS.md](02_DAYPRESS_TECHNICAL_ANALYSIS.md).

---

## 1. Triết lý Thiết kế & Chỉ số Hiệu năng Mục tiêu (SLAs)

* **Đóng gói 1 File duy nhất (Single Binary Deployment):** Toàn bộ Web Server, Database Driver, Media Processor, Plugin Engine và giao diện quản trị React Admin được biên dịch vào 1 file thực thi duy nhất (~18MB – 22MB). Không yêu cầu cài đặt PHP, Node.js hay MySQL trên máy chủ VPS.
* **Mô hình Single-Tenant siêu nhẹ:** Mỗi website chạy một tiến trình độc lập cùng 1 file SQLite riêng biệt, dễ dàng sao lưu hoặc di chuyển sang máy chủ khác chỉ bằng cách copy thư mục.
* **Trải nghiệm Kéo thả chuẩn Flatsome UX Builder:** Toàn bộ cây phân cấp bố cục (`Section -> Row -> Col -> Element`), kho Block và bảng chỉnh sửa thuộc tính (Options Panel) gói gọn trong **1 cột Sidebar bên trái (340px)**. Màn hình bên phải là `iframe` hiển thị giao diện thật 100% do Rust xuất ra, cập nhật DOM mượt mà qua `morphdom` không cần tải lại trang.
* **Chỉ số hiệu năng cam kết trong bản gốc:**
  * **RAM tiêu thụ (Idle/Normal load):** 12MB – 25MB / website.
  * **Thời gian phản hồi Hot Cache (TTFB):** < 50 micro-giây ($\mu s$).
  * **Thời gian kết xuất trang động & Lọc dữ liệu (SSR + SQLite WAL):** < 1 mili-giây ($ms$).
  * **Thời gian cập nhật 1 Node khi sửa trên UX Builder:** < 2 mili-giây ($ms$).

## 2. Kiến trúc Công nghệ Tổng thể (Tech Stack)

| Tầng hệ thống | Công nghệ & Thư viện (Crates / Packages) | Vai trò cốt lõi |
| :--- | :--- | :--- |
| **Core HTTP Server** | **Rust** (`axum`, `tokio`, `tower-http`) | Máy chủ HTTP hiệu năng cao, định tuyến, xác thực, nén Gzip/Brotli |
| **Database Engine** | **SQLite (WAL Mode)** + `sqlx` | Lưu trữ quan hệ kết hợp JSON Indexing, kiểm tra truy vấn an toàn, tự động Migration |
| **Template & SSR** | **`minijinja`** + `serde_json` | Biên dịch cây Nested AST của UX Builder và kết xuất file `.html` của Theme |
| **CSS Generator** | **`encre-css`** (Crate Rust tương thích Tailwind) | Tự động quét class trong `template.html` và sinh CSS tối ưu ngay trong Rust mà không cần Node.js |
| **Hot Cache** | **`dashmap`** + `bytes` + `flate2` | Lưu trữ trang HTML hoàn chỉnh đã nén Gzip ngay trên RAM |
| **Plugin Runtime** | **`rquickjs`** (QuickJS Engine) | Thực thi các file plugin `.js` (`addAction`, `addFilter`) trong môi trường Sandbox cô lập |
| **Media & Updater** | **`image`**, `webp`, `zip`, `self_update` | Tự động cắt và nén ảnh sang WebP, giải nén Theme/Plugin, tự cập nhật file thực thi |
| **Admin & UX Builder** | **React**, **Vite**, **Zustand**, **`@dnd-kit`**, **`morphdom`** | Giao diện quản trị và UX Builder 1 cột trái siêu nhẹ (nhúng vào Rust qua `rust-embed`) |
| **Storefront JS** | **HTMX** (~14KB) + **Alpine.js** (~15KB) | Xử lý giỏ hàng, lọc sản phẩm, chọn biến thể mượt mà không cần tải lại trang |

## 3. Cấu trúc Thư mục Hệ thống

### 3.1. Cấu trúc Mã nguồn khi Phát triển (Development Workspace)

```text
rust-cms-workspace/
├── Cargo.toml
├── ARCHITECTURE.md
├── crates/
│   ├── cms-core/                     # Độc lập với tầng HTTP
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── ast.rs                # Nested JSON AST -> MiniJinja HTML
│   │       ├── hooks.rs              # Action/Filter và QuickJS Sandbox
│   │       ├── theme.rs              # Theme, override, CSS variables, encre-css
│   │       ├── fields.rs             # Validation JSON Custom Fields & SQLite index
│   │       └── media.rs              # Ảnh đa kích thước và WebP
│   └── cms-server/
│       ├── Cargo.toml
│       ├── migrations/
│       │   └── 0001_initial_schema.sql
│       └── src/
│           ├── main.rs               # SQLite WAL & AdminAssets
│           ├── state.rs              # DB Pool, Cache, Jinja Env, Hook Engine
│           ├── cache.rs              # In-memory Gzip Hot Cache & invalidation
│           ├── routes/
│           │   ├── public.rs         # SSR: home, bài viết, danh mục, sản phẩm
│           │   ├── admin_api.rs      # REST Admin & render node
│           │   └── htmx_shop.rs      # Cart & CollectionGrid fragments
│           └── ecommerce/
│               ├── cart.rs
│               ├── checkout.rs       # Transaction khóa tồn kho, tạo đơn
│               └── vietqr.rs         # VietQR & webhook
└── admin-ui/
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── App.tsx
        ├── pages/                    # Dashboard, Entries, Products, Orders,
        │                             # ContentTypes, Themes, Plugins
        └── ux-builder/
            ├── store.ts              # AST, Undo/Redo, Selected Node
            ├── LeftSidebar.tsx       # 340px; Tree / Edit / Add
            ├── LayerTree.tsx         # Section -> Row -> Col; @dnd-kit
            ├── OptionsPanel.tsx      # Form sinh từ schema.json
            ├── ElementPicker.tsx     # Kho Block khi bấm (+)
            └── PreviewIframe.tsx     # postMessage & morphdom
```

### 3.2. Cấu trúc Thư mục trên Máy chủ VPS (Production Runtime)

```text
/var/www/ten-website/
├── cms-server                         # Core + React Admin + UX Builder
├── data/
│   ├── cms.sqlite
│   ├── cms.sqlite-wal
│   └── backups/
├── uploads/                           # Ảnh .webp
├── themes/
│   └── default-shop/
│       ├── theme.json                 # Metadata & Design Tokens
│       ├── screenshot.webp
│       ├── functions.js
│       ├── assets/                    # Fonts, icons, bundle.css
│       ├── layouts/
│       │   └── base.html              # Head, CSS vars, HTMX, {{ body }}
│       ├── templates/                 # AST mặc định
│       │   ├── header.json
│       │   ├── footer.json
│       │   ├── home.json
│       │   ├── single-product.json
│       │   └── archive-product.json
│       └── blocks/
│           ├── section/
│           │   ├── schema.json
│           │   └── template.html      # {{ children | safe }}
│           ├── row/
│           │   ├── schema.json
│           │   └── template.html
│           ├── col/
│           │   ├── schema.json
│           │   └── template.html
│           ├── site-header/
│           │   ├── schema.json
│           │   └── template.html
│           └── product-grid/
│               ├── schema.json
│               └── template.html
└── plugins/
    └── order-telegram-notify/
        ├── plugin.json                # Metadata & quyền hạn
        └── index.js                   # cms.addAction / cms.addFilter
```

## 4. Thiết kế Cơ sở Dữ liệu Toàn diện (`0001_initial_schema.sql`)

> Schema dưới đây là schema của bản thiết kế gốc, được lưu để tham chiếu. Trước khi dùng cho production, áp dụng các thay đổi được giải thích trong file 03; đặc biệt là auth, revisions, constraints, dữ liệu dẫn xuất và kiểu dữ liệu tiền.

```sql
-- Bật chế độ WAL và đồng bộ tối ưu ngay khi khởi tạo
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- 1. BẢNG CẤU HÌNH HỆ THỐNG, THEME & PLUGIN
CREATE TABLE settings (
    key TEXT PRIMARY KEY,               -- site_info, active_theme, theme_styles, active_plugins
    value TEXT NOT NULL,                -- Chuỗi JSON
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. CUSTOM POST TYPES & CUSTOM FIELDS (Zero-Code CPT + ACF)
CREATE TABLE content_types (
    slug TEXT PRIMARY KEY,              -- post, page, portfolio, product
    name TEXT NOT NULL,
    is_hierarchical BOOLEAN DEFAULT 0,
    fields_schema TEXT NOT NULL DEFAULT '[]',
    filterable_fields TEXT NOT NULL DEFAULT '[]'
);

-- 3. TEMPLATE TOÀN TRANG (Header, Footer, Single, Archive)
CREATE TABLE templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theme_id TEXT NOT NULL,
    type TEXT NOT NULL,                 -- header, footer, home, single_post, single_product, archive_product
    name TEXT NOT NULL,
    is_default BOOLEAN DEFAULT 0,
    ast_json TEXT NOT NULL,
    rendered_html TEXT NOT NULL,        -- Chuỗi MiniJinja HTML đã biên dịch sẵn (Dual-Storage)
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 4. BÀI VIẾT, TRANG TĨNH & CUSTOM POST TYPES
CREATE TABLE entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_slug TEXT NOT NULL REFERENCES content_types(slug) ON DELETE CASCADE,
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'publish',      -- publish, draft
    template_id INTEGER REFERENCES templates(id) ON DELETE SET NULL,
    featured_image TEXT,
    ast_json TEXT NOT NULL DEFAULT '[]',
    rendered_html TEXT NOT NULL DEFAULT '',
    custom_fields TEXT NOT NULL DEFAULT '{}',
    seo_meta TEXT NOT NULL DEFAULT '{}',
    published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. PHÂN LOẠI ĐA NĂNG (Categories, Tags, Thuộc tính danh mục)
CREATE TABLE taxonomies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxonomy TEXT NOT NULL,             -- category, product_cat, tag
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    parent_id INTEGER REFERENCES taxonomies(id) ON DELETE SET NULL,
    description TEXT
);

CREATE TABLE term_relationships (
    object_type TEXT NOT NULL,          -- entry hoặc product
    object_id INTEGER NOT NULL,
    taxonomy_id INTEGER NOT NULL REFERENCES taxonomies(id) ON DELETE CASCADE,
    PRIMARY KEY (object_type, object_id, taxonomy_id)
);

-- 6. SẢN PHẨM & BIẾN THỂ SKU
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'publish',
    base_price REAL NOT NULL DEFAULT 0,
    sale_price REAL,
    featured_image TEXT,
    gallery_json TEXT NOT NULL DEFAULT '[]',
    template_id INTEGER REFERENCES templates(id) ON DELETE SET NULL,
    ast_json TEXT NOT NULL DEFAULT '[]',
    rendered_html TEXT NOT NULL DEFAULT '',
    custom_fields TEXT NOT NULL DEFAULT '{}',
    seo_meta TEXT NOT NULL DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    sku TEXT UNIQUE,
    price REAL NOT NULL,
    sale_price REAL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    options_json TEXT NOT NULL DEFAULT '{}'    -- {"Màu sắc": "Đen", "Kích cỡ": "L"}
);

-- 7. GIỎ HÀNG
CREATE TABLE carts (
    session_id TEXT PRIMARY KEY,
    items_json TEXT NOT NULL DEFAULT '[]',     -- [{product_id, variant_id, qty, price_snapshot}]
    coupon_code TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 8. ĐƠN HÀNG
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code TEXT NOT NULL UNIQUE,           -- Ví dụ DH26091 để đối soát VietQR
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    customer_email TEXT,
    customer_address TEXT NOT NULL,
    customer_note TEXT,
    items_snapshot_json TEXT NOT NULL,
    subtotal REAL NOT NULL,
    shipping_fee REAL NOT NULL DEFAULT 0,
    discount_amount REAL NOT NULL DEFAULT 0,
    total_amount REAL NOT NULL,
    payment_method TEXT NOT NULL,              -- COD, VIETQR
    payment_status TEXT DEFAULT 'pending',     -- pending, paid, refunded
    order_status TEXT DEFAULT 'new',           -- new, processing, shipped, completed, cancelled
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- CHỈ MỤC CỐ ĐỊNH
CREATE INDEX idx_templates_lookup ON templates(theme_id, type, is_default);
CREATE INDEX idx_entries_type_status ON entries(type_slug, status);
CREATE INDEX idx_entries_slug ON entries(slug);
CREATE INDEX idx_products_slug_status ON products(slug, status);
CREATE INDEX idx_products_price ON products(base_price);
CREATE INDEX idx_variants_product ON product_variants(product_id);
CREATE INDEX idx_orders_code ON orders(order_code);
CREATE INDEX idx_orders_phone ON orders(customer_phone);
```

## 5. Đặc tả Kỹ thuật 6 Động cơ Lõi (Core Engines)

### 5.1. Động cơ UX Builder (Flatsome Style) & Cây AST Đệ quy (Nested AST)

#### 5.1.1. Cấu trúc Cây JSON Đệ quy (`AstNode`)

Khác với mô hình phẳng, mỗi phần tử trên trang đều tuân theo cấu trúc cây lồng nhau giống UX Builder (`Section -> Row -> Col -> Elements`):

```json
[
  {
    "id": "sec_01",
    "type": "section",
    "label": "Hero Banner",
    "props": { "bg_color": "#f8fafc", "padding_y": 60 },
    "children": [
      {
        "id": "row_01",
        "type": "row",
        "props": { "gap": 24, "align": "center" },
        "children": [
          {
            "id": "col_01",
            "type": "col",
            "props": { "span_desktop": 6, "span_mobile": 12 },
            "children": [
              {
                "id": "el_heading_01",
                "type": "heading",
                "props": { "text": "Bộ sưu tập Mùa Hè", "tag": "h1" },
                "children": []
              }
            ]
          }
        ]
      }
    ]
  }
]
```

#### 5.1.2. Sidebar 1 Cột Trái (340px) trong React Admin

* **Trạng thái 1 – Layer Tree (Mặc định):** Hiển thị cây phân cấp các khối trên trang. Hỗ trợ đóng/mở nhánh (`Collapse/Expand`), kéo thả đổi thứ tự hoặc di chuyển khối giữa các `Col` bằng `@dnd-kit`, nhân bản (`Duplicate`), ẩn/hiện và nút `+` để chèn khối con vào đúng nhánh đang chọn.
* **Trạng thái 2 – Options Panel (Khi click vào 1 Node):** Cột Sidebar trượt sang giao diện chỉnh sửa thuộc tính của khối đó (tự động đọc `schema.json` để render các ô Color Picker, Slider, Media, Repeater) kèm nút `← Quay lại cây cấu trúc` trên thanh tiêu đề.
* **Trạng thái 3 – Element Picker (Khi bấm nút `+`):** Hiển thị danh sách các Block chia theo nhóm (*Layout*, *Content*, *Woo/Shop*) và kiểm tra điều kiện `accepts_children` trong `schema.json`. Ví dụ: bấm `+` ở `Row` thì gợi ý thêm `Col`; bấm `+` ở `Col` thì hiện toàn bộ các khối nội dung và sản phẩm.

#### 5.1.3. Đồng bộ Live Preview qua Iframe + `morphdom` (< 2ms)

* Khi render ở chế độ Preview (`?ux_preview=1`), trình biên dịch Rust tự động gắn thuộc tính `data-ux-id="{{ node.id }}"` và `data-ux-label="{{ node.label }}"` vào thẻ HTML gốc của mỗi Block.
* Một script nhỏ (~2KB) trong `iframe` bắt sự kiện `mouseover` để vẽ đường viền xanh mảnh kèm tên khối và `click` để bắn `window.parent.postMessage({ type: 'UX_SELECT', id })`. Sidebar mở bảng chỉnh sửa tương ứng.
* Khi người dùng thay đổi thông số, React gửi nhánh JSON của Node đang sửa về `POST /api/admin/render-node`. Rust trả về HTML của riêng Node đó trong < 1ms theo mục tiêu bản gốc. Iframe dùng `morphdom` cập nhật đúng thẻ `[data-ux-id="..."]` mà không làm nháy trang hay mất vị trí cuộn.

#### 5.1.4. Biên dịch Lưu kép (Compile-on-Save)

Khi bấm **Lưu (Publish)**, hàm đệ quy `compile_ast_to_html` duyệt từ các Node lá lên Node cha, loại bỏ hoàn toàn các thuộc tính `data-ux-*`, xuất ra chuỗi mẫu MiniJinja sạch lưu vào cột `rendered_html` và chạy `encre-css` để trích xuất CSS ra file `/themes/<active-theme>/assets/bundle.css`.

### 5.2. Động cơ Zero-Code CPT, Custom Fields & CollectionGrid (< 1ms)

#### 5.2.1. Tự động hóa Expression Index trong SQLite

Khi quản trị viên đánh dấu một trường tùy chỉnh (ví dụ `thuong_hieu` hoặc `dien_tich`) là `filterable: true` trên Admin, Rust kiểm tra tên trường bằng biểu thức chính quy `^[a-zA-Z0-9_]+$` và tự động chạy lệnh:

```sql
CREATE INDEX IF NOT EXISTS idx_cf_products_thuong_hieu
ON products(json_extract(custom_fields, '$.thuong_hieu'));
```

#### 5.2.2. Xử lý lọc động qua HTMX

* Khối `CollectionGrid` ngoài trang chủ gắn thuộc tính `hx-get="/api/collections/products"` lên thanh bộ lọc.
* Khi khách hàng tích chọn thương hiệu hoặc kéo thanh trượt giá, HTMX gửi các tham số query về Axum. Axum đối chiếu với danh sách `filterable_fields`, thực thi truy vấn `json_extract` trên chỉ mục đã tạo và trả về HTML danh sách sản phẩm mới trong chưa đầy 1ms theo mục tiêu bản gốc.

### 5.3. Động cơ Theme, CSS Variables & Cơ chế Ghi đè (Template Override)

#### 5.3.1. Thứ tự ưu tiên nạp Block (Fallback Hierarchy)

Khi cần nạp một Block, ví dụ `cart-drawer`, `ThemeLoader` tìm trong `/themes/<active-theme>/blocks/cart-drawer/` trước. Nếu không tồn tại, hệ thống dùng bản mặc định được nhúng sẵn trong Core.

#### 5.3.2. Đồng bộ Design Tokens (`theme.json`)

Các thiết lập màu sắc, font chữ và độ rộng khung trang trong `theme.json` (hoặc bản ghi đè trong bảng `settings` khi người dùng chỉnh qua *Theme Customizer*) được bơm vào thẻ `<style>:root { ... }</style>` trên đầu file `layouts/base.html`.

#### 5.3.3. Bảo toàn dữ liệu khi Cập nhật hoặc Đổi Theme

Các bản chỉnh sửa bố cục Header/Footer/Trang chủ của người dùng được lưu trong bảng `templates` gắn với `theme_id`. Khi cập nhật file `.zip` của Theme, các file `template.html` được nâng cấp nhưng bố cục JSON trong SQLite vẫn giữ nguyên vẹn 100% theo kỳ vọng của bản gốc.

### 5.4. Động cơ E-commerce, Khóa Tồn kho & VietQR Tự động

> Phần này thuộc tầm nhìn mở rộng, chưa nằm trong ưu tiên xây CMS đầu tiên của OpenDash.

#### 5.4.1. Giỏ hàng HTMX siêu nhẹ

Trạng thái giỏ hàng gắn với cookie `cms_cart_session`. Mọi thao tác thêm/sửa/xóa sản phẩm trả về HTML cập nhật trực tiếp ngăn kéo `#cart-drawer` và nhãn số lượng `#cart-badge` thông qua `hx-swap-oob="true"` của HTMX.

#### 5.4.2. Chống âm kho tuyệt đối (Atomic Inventory Deduction)

Tại bước tạo đơn hàng (`POST /api/checkout`), hệ thống mở một `BEGIN IMMEDIATE TRANSACTION` trong SQLite:

```sql
UPDATE product_variants
SET stock_quantity = stock_quantity - ?1
WHERE id = ?2 AND stock_quantity >= ?1;
```

Nếu số dòng bị ảnh hưởng (`rows_affected`) bằng 0, giao dịch lập tức `ROLLBACK` và báo hết hàng. Bản gốc kỳ vọng cơ chế này đảm bảo không bán vượt số lượng tồn kho khi có nhiều người mua cùng lúc.

#### 5.4.3. Tự động hóa VietQR

* Sinh chuỗi ảnh QR theo chuẩn Napas247 chứa sẵn số tiền `total_amount` và nội dung chuyển khoản là `order_code`, ví dụ `DH26091`.
* Cung cấp endpoint `POST /api/webhooks/payment` nhận dữ liệu từ SePay/Casso; khi khớp `order_code` và số tiền, chuyển `payment_status = 'paid'` và kích hoạt hook `order_paid`.

### 5.5. Động cơ Plugin Sandbox (`rquickjs`)

Để đảm bảo tốc độ và chống treo máy chủ, các điểm neo (Hooks) được chia làm 2 cơ chế thực thi:

| Nhóm Hook | Danh sách Hook tiêu chuẩn | Cơ chế thực thi & Giới hạn theo bản gốc |
| :--- | :--- | :--- |
| **Filter Hooks** (Biến đổi dữ liệu) | `before_render_context`, `after_render_html`, `product_display_price`, `cart_calculate_totals` | Chạy đồng bộ trên luồng hiện tại. RAM 8MB, timeout 10ms. Không cho phép gọi mạng HTTP. |
| **Action Hooks** (Sự kiện hậu trường) | `entry_saved`, `order_created`, `order_paid`, `register_custom_routes` | Chạy nền bằng `tokio::spawn` sau khi trả kết quả. RAM 32MB, timeout 5000ms. Cho phép `cms.http` gọi API ngoài như Telegram, Zalo, GiaoHangNhanh. |

### 5.6. Động cơ In-Memory Gzip Hot Cache & Tự động Cập nhật

#### 5.6.1. Lưu trữ byte nén sẵn

Trước khi lưu vào `DashMap<String, Bytes>`, HTML hoàn chỉnh được nén Gzip. Khi có request `GET` từ khách vãng lai không có cookie Admin và giỏ hàng trống, Axum gắn header `Content-Encoding: gzip` và gửi byte từ RAM ra socket mạng trong dưới 50 micro-giây theo mục tiêu bản gốc.

#### 5.6.2. Chiến lược Xóa Cache (Invalidation)

* Lưu bài viết/sản phẩm đơn lẻ: xóa key của URL đó, trang chủ (`/`) và các trang danh mục liên quan.
* Lưu Template toàn cục Header/Footer, đổi `theme.json` hoặc bật/tắt Plugin: gọi `hot_cache.clear()`.

#### 5.6.3. Self-Updating Binary

Khi bấm **Cập nhật hệ thống**, Rust sao lưu `data/cms.sqlite` sang `data/backups/`, tải file thực thi mới, kiểm tra SHA-256, trỏ lại file thực thi hiện hành và tự khởi động lại tiến trình.

## 6. Lộ trình Thực thi Code (4 Cột mốc Triển khai MVP)

> Đây là lịch dự kiến của bản thiết kế đầu tiên, không phải lịch đã chốt sau khi chuyển trọng tâm sang CMS. Lộ trình đề xuất hiện tại nằm ở file 03 và dùng tiêu chí nghiệm thu thay cho cam kết tuần.

* **Cột mốc 1 (Tuần 1–2) – Lõi Server & Đệ quy Nested AST:** Khởi tạo Cargo Workspace, SQLite WAL, migration `0001_initial_schema.sql`, `ThemeLoader`, hàm đệ quy `compile_ast_to_html` hỗ trợ `Section -> Row -> Col` và tích hợp `encre-css`.
* **Cột mốc 2 (Tuần 3–4) – UX Builder Sidebar & Clean Iframe Preview:** Khởi tạo `admin-ui`, Zustand Store, `LeftSidebar.tsx` với LayerTree + OptionsPanel + ElementPicker; `PreviewIframe.tsx` cập nhật DOM bằng morphdom qua `/api/admin/render-node`.
* **Cột mốc 3 (Tuần 5–7) – Zero-Code Custom Fields & Lõi E-commerce:** Giao diện tạo Custom Fields, CollectionGrid, quản lý Sản phẩm/Biến thể, Giỏ hàng HTMX và Thanh toán VietQR.
* **Cột mốc 4 (Tuần 8–10) – QuickJS Plugin, Media WebP & Đóng gói:** `rquickjs` cho Action/Filter, upload ZIP Theme/Plugin, WebP tự động, DashMap Hot Cache và binary nhúng Admin qua `rust-embed`.

## 7. Ghi chú biên tập

Nội dung kỹ thuật của bản gốc được giữ làm đường cơ sở; một số chú thích cây thư mục và SQL được trình bày lại cho dễ đọc, không đổi định nghĩa bảng, cột hay index. Các điểm cần điều chỉnh không được ngầm coi là đã sửa trong schema này. Dùng file 03 để theo dõi đề xuất, phần đã thống nhất và các quyết định còn mở.
