mod theme;

use std::{collections::BTreeMap, env, net::Ipv4Addr, path::PathBuf, time::Duration};

use axum::{
    Json, Router,
    body::Bytes,
    extract::{DefaultBodyLimit, Request, State},
    http::{HeaderMap, StatusCode, header},
    middleware::{self, Next},
    response::{Html, IntoResponse, Response},
    routing::{get, post},
};
use sqlx::{
    SqlitePool,
    sqlite::{SqliteConnectOptions, SqliteJournalMode, SqlitePoolOptions},
};

use theme::{Block, Fields, MAX_ZIP_BYTES, Theme};

const BUILDER: &str = include_str!("../spikes/stack-v1/builder.html");

struct ApiError(StatusCode, &'static str);
type ApiResult<T> = Result<T, ApiError>;

impl ApiError {
    fn bad_request(message: &'static str) -> Self {
        Self(StatusCode::BAD_REQUEST, message)
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        (self.0, self.1).into_response()
    }
}

impl From<sqlx::Error> for ApiError {
    fn from(error: sqlx::Error) -> Self {
        eprintln!("SQLite: {error}");
        Self(
            StatusCode::INTERNAL_SERVER_ERROR,
            "Không truy cập được dữ liệu.",
        )
    }
}

impl From<serde_json::Error> for ApiError {
    fn from(error: serde_json::Error) -> Self {
        eprintln!("JSON: {error}");
        Self(
            StatusCode::INTERNAL_SERVER_ERROR,
            "Dữ liệu block không hợp lệ.",
        )
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let db_path = PathBuf::from(
        env::var_os("OPENDASH_DB_PATH").unwrap_or_else(|| "data/opendash.sqlite".into()),
    );
    if let Some(parent) = db_path
        .parent()
        .filter(|parent| !parent.as_os_str().is_empty())
    {
        std::fs::create_dir_all(parent)?;
    }
    let options = SqliteConnectOptions::new()
        .filename(db_path)
        .create_if_missing(true)
        .foreign_keys(true)
        .journal_mode(SqliteJournalMode::Wal)
        .busy_timeout(Duration::from_secs(5));
    let db = SqlitePoolOptions::new()
        .max_connections(2)
        .connect_with(options)
        .await?;
    sqlx::migrate!().run(&db).await?;

    let port = env::var("OPENDASH_PORT")
        .unwrap_or_else(|_| "18766".into())
        .parse::<u16>()?;
    let listener = tokio::net::TcpListener::bind((Ipv4Addr::LOCALHOST, port)).await?;
    let address = listener.local_addr()?;
    let expected_host = address.to_string();
    let app = Router::new()
        .route("/", get(public_page))
        .route("/builder", get(|| async { Html(BUILDER) }))
        .route("/registry", get(registry))
        .route("/page", get(page))
        .route("/theme", post(install))
        .route("/preview", post(preview))
        .route("/save", post(save))
        .layer(DefaultBodyLimit::max(MAX_ZIP_BYTES))
        .layer(middleware::from_fn(move |request: Request, next: Next| {
            let valid = request
                .headers()
                .get(header::HOST)
                .and_then(|h| h.to_str().ok())
                == Some(expected_host.as_str());
            async move {
                if valid {
                    next.run(request).await
                } else {
                    StatusCode::BAD_REQUEST.into_response()
                }
            }
        }))
        .with_state(db);
    println!("OpenDash: http://{address}/builder");
    axum::serve(listener, app).await?;
    Ok(())
}

async fn registry(State(db): State<SqlitePool>) -> ApiResult<Json<BTreeMap<String, Fields>>> {
    let rows: Vec<(String, String)> = sqlx::query_as("SELECT id, fields_json FROM theme_blocks")
        .fetch_all(&db)
        .await?;
    let blocks = rows
        .into_iter()
        .map(|(id, fields)| Ok((id, serde_json::from_str(&fields)?)))
        .collect::<Result<_, serde_json::Error>>()?;
    Ok(Json(blocks))
}

async fn install(
    State(db): State<SqlitePool>,
    headers: HeaderMap,
    bytes: Bytes,
) -> ApiResult<StatusCode> {
    if headers
        .get(header::CONTENT_TYPE)
        .and_then(|value| value.to_str().ok())
        != Some("application/zip")
    {
        return Err(ApiError(
            StatusCode::UNSUPPORTED_MEDIA_TYPE,
            "Cần gói application/zip.",
        ));
    }
    let theme = Theme::from_zip(&bytes).map_err(ApiError::bad_request)?;
    let result =
        sqlx::query("INSERT INTO theme_blocks (id, fields_json, template) VALUES (?, ?, ?)")
            .bind(theme.descriptor.id)
            .bind(serde_json::to_string(&theme.descriptor.fields)?)
            .bind(theme.template)
            .execute(&db)
            .await;
    match result {
        Err(sqlx::Error::Database(error)) if error.is_unique_violation() => Err(ApiError(
            StatusCode::CONFLICT,
            "ID block đã có trong dữ liệu.",
        )),
        result => {
            result?;
            Ok(StatusCode::CREATED)
        }
    }
}

async fn page(State(db): State<SqlitePool>) -> ApiResult<Json<Option<Block>>> {
    Ok(Json(load_page(&db).await?))
}

async fn load_page(db: &SqlitePool) -> ApiResult<Option<Block>> {
    let row: Option<(String, String)> =
        sqlx::query_as("SELECT block_id, values_json FROM home_page WHERE id = 1")
            .fetch_optional(db)
            .await?;
    row.map(|(kind, values)| {
        Ok(Block {
            kind,
            values: serde_json::from_str(&values)?,
        })
    })
    .transpose()
}

async fn public_page(State(db): State<SqlitePool>) -> ApiResult<Response> {
    let html = match load_page(&db).await? {
        Some(block) => render_block(&db, &block).await?,
        None => "<p>Chưa lưu block.</p>".into(),
    };
    Ok(rendered(html))
}

async fn preview(State(db): State<SqlitePool>, Json(block): Json<Block>) -> ApiResult<Response> {
    Ok(rendered(render_block(&db, &block).await?))
}

async fn save(State(db): State<SqlitePool>, Json(block): Json<Block>) -> ApiResult<Response> {
    let html = render_block(&db, &block).await?;
    sqlx::query(
        "INSERT INTO home_page (id, block_id, values_json) VALUES (1, ?, ?)
         ON CONFLICT(id) DO UPDATE SET block_id = excluded.block_id, values_json = excluded.values_json",
    )
    .bind(block.kind)
    .bind(serde_json::to_string(&block.values)?)
    .execute(&db)
    .await?;
    Ok(rendered(html))
}

async fn render_block(db: &SqlitePool, block: &Block) -> ApiResult<String> {
    let row: Option<(String, String)> =
        sqlx::query_as("SELECT template, fields_json FROM theme_blocks WHERE id = ?")
            .bind(&block.kind)
            .fetch_optional(db)
            .await?;
    let (template, fields) = row.ok_or(ApiError::bad_request("Không tìm thấy block."))?;
    theme::render(&template, &serde_json::from_str(&fields)?, block).map_err(ApiError::bad_request)
}

fn rendered(html: String) -> Response {
    (
        [
            (
                header::CONTENT_SECURITY_POLICY,
                "sandbox; default-src 'none'",
            ),
            (header::X_CONTENT_TYPE_OPTIONS, "nosniff"),
        ],
        Html(html),
    )
        .into_response()
}
