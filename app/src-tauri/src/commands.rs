//! Tauri commands exposed to the React frontend.

use std::path::PathBuf;

use tauri::AppHandle;
use tauri_plugin_autostart::ManagerExt;
use tauri_plugin_opener::OpenerExt;

use crate::hotkeys;
use crate::paste;
use crate::storage::{self, AppSettings, Placeholder, Preset};
use crate::trash::{self, TrashEntry};

const EXPORT_VERSION: &str = "1.0.0";
const SHORTCUT_REL: &str = "Microsoft\\Windows\\Start Menu\\Programs\\HKI.lnk";
/// Soft cap on trash.json. Entries beyond this are dropped oldest-first.
const TRASH_MAX_ENTRIES: usize = 200;

fn shortcut_path() -> Result<PathBuf, String> {
    let roaming = std::env::var_os("APPDATA")
        .map(PathBuf::from)
        .or_else(dirs::data_dir)
        .ok_or_else(|| "could not locate %APPDATA%".to_string())?;
    Ok(roaming.join(SHORTCUT_REL))
}

fn err<E: std::fmt::Display>(e: E) -> String {
    e.to_string()
}

#[tauri::command]
pub fn load_presets() -> Result<Vec<Preset>, String> {
    storage::load_presets().map_err(err)
}

#[tauri::command]
pub fn save_presets(presets: Vec<Preset>) -> Result<(), String> {
    storage::save_presets(&presets).map_err(err)
}

#[tauri::command]
pub fn register_hotkeys(app: AppHandle, presets: Vec<Preset>) -> Result<Vec<String>, String> {
    // Pick up whatever summon hotkey is on disk so registration stays in
    // sync without forcing the frontend to thread it through.
    let settings = storage::load_settings().unwrap_or_default();
    Ok(hotkeys::register_all(
        &app,
        &presets,
        &settings.sidebar_hotkey,
    ))
}

#[tauri::command]
pub fn paste_preset(app: AppHandle, preset_id: String) -> Result<(), String> {
    let presets = storage::load_presets().map_err(err)?;
    let preset = presets
        .into_iter()
        .find(|p| p.id == preset_id)
        .ok_or_else(|| format!("preset '{preset_id}' not found"))?;
    paste::paste_text(&app, &preset.text).map_err(err)
}

#[tauri::command]
pub fn load_settings() -> Result<AppSettings, String> {
    storage::load_settings().map_err(err)
}

#[tauri::command]
pub fn save_settings(app: AppHandle, settings: AppSettings) -> Result<(), String> {
    // Only re-register hotkeys when `sidebar_hotkey` actually changed.
    // Without this guard, every keystroke in the Formats / Custom
    // placeholder fields would tear down and rebuild every global
    // shortcut — noisy, and risks transient collision errors.
    let prev_sidebar = storage::load_settings()
        .map(|s| s.sidebar_hotkey)
        .unwrap_or_default();
    storage::save_settings(&settings).map_err(err)?;
    if prev_sidebar != settings.sidebar_hotkey {
        let presets = storage::load_presets().unwrap_or_default();
        let _ = hotkeys::register_all(&app, &presets, &settings.sidebar_hotkey);
    }
    Ok(())
}

#[tauri::command]
pub fn set_autostart(app: AppHandle, enabled: bool) -> Result<(), String> {
    let manager = app.autolaunch();
    if enabled {
        manager.enable().map_err(err)?;
    } else {
        manager.disable().map_err(err)?;
    }
    let mut current = storage::load_settings().unwrap_or_default();
    current.autostart = enabled;
    storage::save_settings(&current).map_err(err)?;
    Ok(())
}

/// Open a URL or — with no argument — the HKI data directory in the system
/// file manager. Only whitelisted schemes are accepted so a rogue frontend
/// can't ask us to launch arbitrary executables.
#[tauri::command]
pub fn open_url(app: AppHandle, url: String) -> Result<(), String> {
    let target = if url.is_empty() {
        storage::data_dir()
            .map_err(err)?
            .to_string_lossy()
            .into_owned()
    } else {
        let lower = url.to_ascii_lowercase();
        let allowed = lower.starts_with("http://")
            || lower.starts_with("https://")
            || lower.starts_with("mailto:");
        if !allowed {
            return Err(format!("refused to open disallowed URL scheme: {url}"));
        }
        url
    };
    app.opener().open_path(target, None::<&str>).map_err(err)
}

/// Serialise the given presets to an `.hki` JSON file at the user-chosen
/// path. The path comes from a native save-file dialog triggered from the
/// frontend, so the user has already consented to the destination.
#[tauri::command]
pub fn export_presets_to_path(path: String, presets: Vec<Preset>) -> Result<(), String> {
    let body = serde_json::json!({
        "hki_version": EXPORT_VERSION,
        "presets": presets,
    });
    let pretty = serde_json::to_string_pretty(&body).map_err(err)?;
    std::fs::write(PathBuf::from(path), pretty).map_err(err)?;
    Ok(())
}

/// Read the `.hki` file at the user-chosen path and return its presets
/// with fresh ids so they can't collide with existing entries. Accepts
/// either the versioned `{ hki_version, presets }` envelope or a bare
/// array of presets.
#[tauri::command]
pub fn import_presets_from_path(path: String) -> Result<Vec<Preset>, String> {
    let raw = std::fs::read_to_string(PathBuf::from(path)).map_err(err)?;
    let value: serde_json::Value = serde_json::from_str(&raw).map_err(err)?;
    let rows: Vec<serde_json::Value> = match value {
        serde_json::Value::Array(items) => items,
        serde_json::Value::Object(ref map) => map
            .get("presets")
            .and_then(|v| v.as_array())
            .cloned()
            .ok_or_else(|| "file does not contain a 'presets' array".to_string())?,
        _ => return Err("unexpected JSON shape".to_string()),
    };

    let mut out = Vec::with_capacity(rows.len());
    for row in rows {
        let name = row
            .get("name")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
        let text = row
            .get("text")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
        let placeholders = row
            .get("placeholders")
            .and_then(|v| v.as_array())
            .map(|arr| {
                arr.iter()
                    .map(|ph| Placeholder {
                        id: uuid::Uuid::new_v4().to_string(),
                        key: ph
                            .get("key")
                            .and_then(|v| v.as_str())
                            .unwrap_or("")
                            .to_string(),
                        label: ph
                            .get("label")
                            .and_then(|v| v.as_str())
                            .unwrap_or("")
                            .to_string(),
                    })
                    .collect()
            })
            .unwrap_or_default();
        out.push(Preset {
            id: uuid::Uuid::new_v4().to_string(),
            name,
            hotkey: String::new(), // reset hotkey on import to avoid conflicts
            text,
            placeholders,
        });
    }
    Ok(out)
}

// --- Install / uninstall ---------------------------------------------
//
// The shortcut lives in the per-user Start Menu so installation never
// requires admin rights. It points at wherever `HKI.exe` currently
// lives — the user can run the binary from any folder.

#[tauri::command]
pub fn is_installed() -> Result<bool, String> {
    Ok(shortcut_path()?.exists())
}

#[tauri::command]
pub fn install_shortcut() -> Result<(), String> {
    use std::os::windows::process::CommandExt;

    let exe = std::env::current_exe().map_err(err)?;
    let work_dir = exe
        .parent()
        .map(|p| p.to_path_buf())
        .unwrap_or_else(|| PathBuf::from("."));
    let link = shortcut_path()?;
    if let Some(parent) = link.parent() {
        std::fs::create_dir_all(parent).map_err(err)?;
    }

    // Escape single-quotes for the PowerShell string literals below.
    let esc = |s: &str| s.replace('\'', "''");
    let link_s = esc(&link.to_string_lossy());
    let target_s = esc(&exe.to_string_lossy());
    let work_s = esc(&work_dir.to_string_lossy());

    let ps = format!(
        "$ws = New-Object -ComObject WScript.Shell; \
         $sc = $ws.CreateShortcut('{link_s}'); \
         $sc.TargetPath = '{target_s}'; \
         $sc.WorkingDirectory = '{work_s}'; \
         $sc.IconLocation = '{target_s},0'; \
         $sc.Description = 'HKI - HotKey Input'; \
         $sc.Save()"
    );

    const CREATE_NO_WINDOW: u32 = 0x08000000;
    let status = std::process::Command::new("powershell")
        .args(["-NoProfile", "-Command", &ps])
        .creation_flags(CREATE_NO_WINDOW)
        .status()
        .map_err(err)?;
    if !status.success() {
        return Err(format!(
            "PowerShell shortcut creation exited with status {status}"
        ));
    }
    Ok(())
}

#[tauri::command]
pub fn uninstall_shortcut() -> Result<(), String> {
    let link = shortcut_path()?;
    if link.exists() {
        std::fs::remove_file(&link).map_err(err)?;
    }
    Ok(())
}

// --- Trash bin -------------------------------------------------------
//
// The frontend owns the source of truth for the live preset list. These
// commands only manage `%LOCALAPPDATA%\HKI\trash.json`; after a restore
// the frontend is expected to call `save_presets` + `register_hotkeys`
// itself.

#[tauri::command]
pub fn get_trash() -> Result<Vec<TrashEntry>, String> {
    let _guard = trash::lock();
    trash::load().map_err(err)
}

#[tauri::command]
pub fn trash_preset(preset: Preset) -> Result<(), String> {
    let _guard = trash::lock();
    let mut entries = trash::load().map_err(err)?;
    // Same preset id deleted twice should not end up with two entries —
    // drop the existing one so the new timestamp wins.
    entries.retain(|e| e.preset.id != preset.id);
    let entry = TrashEntry {
        preset,
        deleted_at: chrono::Utc::now().to_rfc3339(),
    };
    entries.insert(0, entry);
    if entries.len() > TRASH_MAX_ENTRIES {
        entries.truncate(TRASH_MAX_ENTRIES);
    }
    trash::save(&entries).map_err(err)
}

#[tauri::command]
pub fn restore_from_trash(id: String) -> Result<Preset, String> {
    let _guard = trash::lock();
    let mut entries = trash::load().map_err(err)?;
    let position = entries
        .iter()
        .position(|e| e.preset.id == id)
        .ok_or_else(|| format!("trash entry for preset '{id}' not found"))?;
    let entry = entries.remove(position);
    trash::save(&entries).map_err(err)?;
    Ok(entry.preset)
}

#[tauri::command]
pub fn purge_from_trash(id: String) -> Result<(), String> {
    let _guard = trash::lock();
    let mut entries = trash::load().map_err(err)?;
    let before = entries.len();
    entries.retain(|e| e.preset.id != id);
    if entries.len() == before {
        return Err(format!("trash entry for preset '{id}' not found"));
    }
    trash::save(&entries).map_err(err)
}

#[tauri::command]
pub fn empty_trash() -> Result<(), String> {
    let _guard = trash::lock();
    trash::save(&[]).map_err(err)
}

/// Full uninstall: remove the Start Menu shortcut, delete the
/// `%LOCALAPPDATA%\HKI` data directory, then exit the app. The binary
/// itself is left in place — the user can delete it manually.
#[tauri::command]
pub fn uninstall_app(app: AppHandle) -> Result<(), String> {
    // Best-effort shortcut removal — don't fail the whole uninstall if
    // the user already deleted it by hand.
    let _ = uninstall_shortcut();

    let dir = storage::data_dir().map_err(err)?;
    if dir.exists() {
        std::fs::remove_dir_all(&dir).map_err(err)?;
    }

    app.exit(0);
    Ok(())
}
