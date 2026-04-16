//! On-disk persistence for presets and settings.
//!
//! Files live under `%LOCALAPPDATA%\HKI\`.

use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Placeholder {
    pub id: String,
    pub key: String,
    pub label: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Preset {
    pub id: String,
    pub name: String,
    pub hotkey: String,
    pub text: String,
    #[serde(default)]
    pub placeholders: Vec<Placeholder>,
}

/// Settings-level placeholder that applies across every preset.
///
/// `kind` is either `"text"` (verbatim insertion of `value`) or
/// `"datetime"` (interpret `value` as a `chrono` strftime pattern and
/// substitute the current local time).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CustomPlaceholder {
    pub id: String,
    pub key: String,
    pub kind: String,
    pub value: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AppSettings {
    #[serde(default = "default_true")]
    pub close_to_tray: bool,
    #[serde(default)]
    pub minimize_to_tray: bool,
    #[serde(default = "default_sidebar_hotkey")]
    pub sidebar_hotkey: String,
    #[serde(default)]
    pub autostart: bool,
    #[serde(default = "default_language")]
    pub language: String,
    #[serde(default = "default_date_format")]
    pub date_format: String,
    #[serde(default = "default_time_format")]
    pub time_format: String,
    #[serde(default)]
    pub custom_placeholders: Vec<CustomPlaceholder>,
}

fn default_true() -> bool {
    true
}

fn default_sidebar_hotkey() -> String {
    "Ctrl+Shift+Space".to_string()
}

fn default_language() -> String {
    "en".to_string()
}

fn default_date_format() -> String {
    "%d.%m.%Y".to_string()
}

fn default_time_format() -> String {
    "%H:%M".to_string()
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            close_to_tray: true,
            minimize_to_tray: false,
            sidebar_hotkey: default_sidebar_hotkey(),
            autostart: false,
            language: default_language(),
            date_format: default_date_format(),
            time_format: default_time_format(),
            custom_placeholders: Vec::new(),
        }
    }
}

pub fn data_dir() -> Result<PathBuf> {
    let base = dirs::data_local_dir()
        .or_else(dirs::home_dir)
        .context("could not locate %LOCALAPPDATA%")?;
    let dir = base.join("HKI");
    fs::create_dir_all(&dir).with_context(|| format!("create {}", dir.display()))?;
    Ok(dir)
}

pub fn presets_path() -> Result<PathBuf> {
    Ok(data_dir()?.join("presets.json"))
}

fn presets_backup_path() -> Result<PathBuf> {
    Ok(data_dir()?.join("presets.json.bak"))
}

pub fn settings_path() -> Result<PathBuf> {
    Ok(data_dir()?.join("settings.json"))
}

fn parse_presets_file(path: &Path) -> Result<Option<Vec<Preset>>> {
    if !path.exists() {
        return Ok(None);
    }
    let raw = fs::read_to_string(path).with_context(|| format!("read {}", path.display()))?;
    if raw.trim().is_empty() {
        return Ok(None);
    }
    let parsed: Vec<Preset> =
        serde_json::from_str(&raw).with_context(|| format!("parse {}", path.display()))?;
    Ok(Some(parsed))
}

pub fn load_presets() -> Result<Vec<Preset>> {
    let primary = presets_path()?;
    match parse_presets_file(&primary) {
        Ok(Some(p)) => Ok(p),
        Ok(None) => {
            // Primary file missing or empty — try the backup silently.
            let backup = presets_backup_path()?;
            match parse_presets_file(&backup) {
                Ok(Some(p)) => {
                    log::warn!(
                        "presets.json missing or empty; recovered {} preset(s) from presets.json.bak",
                        p.len()
                    );
                    Ok(p)
                }
                _ => Ok(Vec::new()),
            }
        }
        Err(primary_err) => {
            // Primary file exists but failed to parse — fall back to .bak
            // if it's usable, otherwise surface the original error.
            let backup = presets_backup_path()?;
            match parse_presets_file(&backup) {
                Ok(Some(p)) => {
                    log::warn!(
                        "presets.json failed to parse ({primary_err:#}); recovered {} preset(s) from presets.json.bak",
                        p.len()
                    );
                    Ok(p)
                }
                _ => Err(primary_err),
            }
        }
    }
}

pub fn save_presets(presets: &[Preset]) -> Result<()> {
    let path = presets_path()?;
    let backup = presets_backup_path()?;
    // Rotate the existing file to .bak so a botched write (or an accidental
    // mass-delete) leaves the user one step of recovery.
    if path.exists() {
        if backup.exists() {
            let _ = fs::remove_file(&backup);
        }
        if let Err(e) = fs::copy(&path, &backup) {
            log::warn!(
                "could not copy {} to {}: {e}",
                path.display(),
                backup.display()
            );
        }
    }
    let body = serde_json::to_string_pretty(presets).context("serialise presets")?;
    atomic_write(&path, body.as_bytes())
}

pub fn load_settings() -> Result<AppSettings> {
    let p = settings_path()?;
    if !p.exists() {
        return Ok(AppSettings::default());
    }
    let raw = fs::read_to_string(&p).with_context(|| format!("read {}", p.display()))?;
    if raw.trim().is_empty() {
        return Ok(AppSettings::default());
    }
    let parsed: AppSettings =
        serde_json::from_str(&raw).with_context(|| format!("parse {}", p.display()))?;
    Ok(parsed)
}

pub fn save_settings(settings: &AppSettings) -> Result<()> {
    let path = settings_path()?;
    let body = serde_json::to_string_pretty(settings).context("serialise settings")?;
    atomic_write(&path, body.as_bytes())
}

pub fn atomic_write(target: &std::path::Path, bytes: &[u8]) -> Result<()> {
    let parent = target.parent().context("target has no parent directory")?;
    fs::create_dir_all(parent).with_context(|| format!("create {}", parent.display()))?;
    let tmp = target.with_extension("tmp");
    {
        let mut f = fs::File::create(&tmp).with_context(|| format!("create {}", tmp.display()))?;
        f.write_all(bytes)
            .with_context(|| format!("write {}", tmp.display()))?;
        f.sync_all().ok();
    }
    // On Windows, rename fails if the destination exists — remove first.
    if target.exists() {
        fs::remove_file(target).with_context(|| format!("remove {}", target.display()))?;
    }
    fs::rename(&tmp, target)
        .with_context(|| format!("rename {} -> {}", tmp.display(), target.display()))?;
    Ok(())
}
