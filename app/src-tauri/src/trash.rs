//! Trash bin for deleted presets.
//!
//! Entries live at `%LOCALAPPDATA%\HKI\trash.json` as a JSON array.
//! Entries are keyed by the preset's own id — one entry per preset.

use std::fs;
use std::path::PathBuf;
use std::sync::Mutex;

use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

use crate::storage::{self, Preset};

/// Serialises concurrent load-mutate-save sequences on `trash.json`.
/// Tauri commands can land on different threadpool workers, so rapid
/// delete/undo races would otherwise overwrite each other's writes.
static TRASH_LOCK: Mutex<()> = Mutex::new(());

/// Acquires the trash file lock for the lifetime of the returned guard.
/// Callers should scope it around the full read-modify-write cycle.
pub fn lock() -> std::sync::MutexGuard<'static, ()> {
    TRASH_LOCK.lock().unwrap_or_else(|poisoned| poisoned.into_inner())
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TrashEntry {
    pub preset: Preset,
    /// ISO-8601 UTC timestamp, e.g. `2026-04-16T21:50:00Z`.
    pub deleted_at: String,
}

fn trash_path() -> Result<PathBuf> {
    Ok(storage::data_dir()?.join("trash.json"))
}

pub fn load() -> Result<Vec<TrashEntry>> {
    let path = trash_path()?;
    if !path.exists() {
        return Ok(Vec::new());
    }
    let raw = match fs::read_to_string(&path) {
        Ok(s) => s,
        Err(e) => {
            log::warn!("could not read {}: {e}", path.display());
            return Ok(Vec::new());
        }
    };
    if raw.trim().is_empty() {
        return Ok(Vec::new());
    }
    match serde_json::from_str::<Vec<TrashEntry>>(&raw) {
        Ok(entries) => Ok(entries),
        Err(e) => {
            log::warn!("could not parse {}: {e}", path.display());
            Ok(Vec::new())
        }
    }
}

pub fn save(entries: &[TrashEntry]) -> Result<()> {
    let path = trash_path()?;
    let body = serde_json::to_string_pretty(entries).context("serialise trash")?;
    storage::atomic_write(&path, body.as_bytes())
}

/// Drop every trash entry whose `deleted_at` is older than `days` days.
/// Entries with unparseable timestamps are treated as fresh and kept, so a
/// malformed file never silently eats data.
pub fn purge_older_than(days: i64) -> Result<usize> {
    let entries = load()?;
    let before = entries.len();
    let cutoff = Utc::now() - chrono::Duration::days(days);
    let kept: Vec<TrashEntry> = entries
        .into_iter()
        .filter(|e| match DateTime::parse_from_rfc3339(&e.deleted_at) {
            Ok(ts) => ts.with_timezone(&Utc) >= cutoff,
            Err(_) => true,
        })
        .collect();
    let removed = before - kept.len();
    if removed > 0 {
        save(&kept)?;
    }
    Ok(removed)
}
