use std::{
    collections::BTreeMap,
    io::{Cursor, Read},
};

use minijinja::{AutoEscape, Environment, UndefinedBehavior};
use serde::{Deserialize, Serialize};
use zip::ZipArchive;

pub const MAX_ZIP_BYTES: usize = 64 * 1024;
pub type Fields = BTreeMap<String, String>;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BlockDescriptor {
    pub id: String,
    pub fields: Fields,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Block {
    #[serde(rename = "type")]
    pub kind: String,
    pub values: Fields,
}

pub struct Theme {
    pub descriptor: BlockDescriptor,
    pub template: String,
}

impl Theme {
    pub fn from_zip(bytes: &[u8]) -> Result<Self, &'static str> {
        if bytes.len() > MAX_ZIP_BYTES {
            return Err("ZIP vượt quá giới hạn kích thước.");
        }

        let mut archive = ZipArchive::new(Cursor::new(bytes)).map_err(|_| "ZIP không hợp lệ.")?;
        if archive.len() != 2 {
            return Err("ZIP phải chứa block.json và block.html.");
        }

        let mut descriptor = None;
        let mut template = None;
        let mut remaining = MAX_ZIP_BYTES;
        for index in 0..archive.len() {
            let entry = archive.by_index(index).map_err(|_| "Không đọc được ZIP.")?;
            let name = entry.name().map_err(|_| "Tên mục ZIP không hợp lệ.")?;
            let slot = match name.as_ref() {
                "block.json" if descriptor.is_none() => &mut descriptor,
                "block.html" if template.is_none() => &mut template,
                _ => return Err("ZIP chứa đường dẫn lạ hoặc mục bị trùng."),
            };
            if entry.size() > remaining as u64 {
                return Err("Nội dung ZIP vượt quá giới hạn kích thước.");
            }
            let mut content = String::new();
            entry
                .take(remaining as u64 + 1)
                .read_to_string(&mut content)
                .map_err(|_| "Không đọc được nội dung ZIP dạng UTF-8.")?;
            remaining = remaining
                .checked_sub(content.len())
                .ok_or("Nội dung ZIP vượt quá giới hạn kích thước.")?;
            *slot = Some(content);
        }

        let descriptor: BlockDescriptor =
            serde_json::from_str(&descriptor.ok_or("Thiếu block.json.")?)
                .map_err(|_| "block.json không hợp lệ.")?;
        let (namespace, name) = descriptor
            .id
            .split_once('/')
            .ok_or("ID block không hợp lệ.")?;
        if !valid_name(namespace, b'-') || !valid_name(name, b'-') {
            return Err("ID block không hợp lệ.");
        }
        if descriptor.fields.is_empty()
            || descriptor.fields.len() > 12
            || descriptor.fields.iter().any(|(key, label)| {
                !valid_name(key, b'_') || label.trim().is_empty() || label.chars().count() > 80
            })
        {
            return Err("Khai báo field không hợp lệ.");
        }

        let template = template.ok_or("Thiếu block.html.")?;
        if template.trim().is_empty() || environment().template_from_str(&template).is_err() {
            return Err("Template block không hợp lệ.");
        }
        Ok(Self {
            descriptor,
            template,
        })
    }
}

pub fn render(template: &str, fields: &Fields, block: &Block) -> Result<String, &'static str> {
    if block.values.keys().ne(fields.keys())
        || block
            .values
            .values()
            .any(|value| value.chars().count() > 512)
    {
        return Err("Giá trị nhập không khớp khai báo block.");
    }
    let env = environment();
    env.template_from_str(template)
        .and_then(|template| template.render(minijinja::context!(values => &block.values)))
        .map_err(|_| "Không render được template block.")
}

fn environment() -> Environment<'static> {
    let mut env = Environment::new();
    env.set_auto_escape_callback(|_| AutoEscape::Html);
    env.set_undefined_behavior(UndefinedBehavior::Strict);
    env.set_fuel(Some(10_000));
    env
}

fn valid_name(value: &str, separator: u8) -> bool {
    value.len() <= 32
        && value.as_bytes().first().is_some_and(u8::is_ascii_lowercase)
        && value
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == separator)
}
