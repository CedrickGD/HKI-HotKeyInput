//! Global hotkey registry. Wraps `tauri-plugin-global-shortcut` and maps a
//! triggered shortcut back to the preset it belongs to.

use std::collections::HashMap;
use std::sync::Mutex;

use tauri::async_runtime;
use tauri::{AppHandle, Manager};
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut, ShortcutState};

use crate::hotkey_parse;
use crate::storage::Preset;

/// Maps `Shortcut::id()` (u32) to the preset id that should fire, plus the
/// separate "summon" shortcut (sidebar_hotkey) which brings the main
/// window to the front.
pub struct HotkeyState {
    mapping: Mutex<HashMap<u32, String>>,
    sidebar_id: Mutex<Option<u32>>,
}

impl HotkeyState {
    pub fn new() -> Self {
        Self {
            mapping: Mutex::new(HashMap::new()),
            sidebar_id: Mutex::new(None),
        }
    }

    pub fn preset_id_for(&self, shortcut: &Shortcut) -> Option<String> {
        self.mapping.lock().ok()?.get(&shortcut.id()).cloned()
    }

    pub fn is_sidebar(&self, shortcut: &Shortcut) -> bool {
        self.sidebar_id
            .lock()
            .ok()
            .and_then(|g| *g)
            .is_some_and(|id| id == shortcut.id())
    }
}

impl Default for HotkeyState {
    fn default() -> Self {
        Self::new()
    }
}

/// Clear all existing registrations and register the ones in `presets`
/// plus the optional "summon" sidebar hotkey. Returns human-readable
/// warnings for invalid syntax, duplicates, and OS-level conflicts.
pub fn register_all(app: &AppHandle, presets: &[Preset], sidebar_hotkey: &str) -> Vec<String> {
    let mut warnings = Vec::new();
    let shortcut_plugin = app.global_shortcut();

    // Unregister everything we knew about. `unregister_all` clears the lot.
    if let Err(e) = shortcut_plugin.unregister_all() {
        warnings.push(format!("Failed to clear previous hotkeys: {e}"));
    }

    let state = app.state::<HotkeyState>();
    if let Ok(mut map) = state.mapping.lock() {
        map.clear();
    }
    if let Ok(mut sid) = state.sidebar_id.lock() {
        *sid = None;
    }

    // Dedup key used for "someone already reserved this combo" — starts
    // with the sidebar hotkey if one is provided so a preset can't steal
    // it.
    let mut seen_ids: HashMap<u32, String> = HashMap::new();

    if !sidebar_hotkey.trim().is_empty() {
        match hotkey_parse::parse(sidebar_hotkey) {
            Ok(parsed) => match shortcut_plugin.register(parsed) {
                Ok(()) => {
                    if let Ok(mut sid) = state.sidebar_id.lock() {
                        *sid = Some(parsed.id());
                    }
                    seen_ids.insert(parsed.id(), "(summon)".to_string());
                }
                Err(e) => warnings.push(format!(
                    "Could not register summon hotkey {}: {e}",
                    hotkey_parse::display(sidebar_hotkey),
                )),
            },
            Err(e) => warnings.push(format!("Invalid summon hotkey '{sidebar_hotkey}': {e}")),
        }
    }

    // Presets share the dedup table with the sidebar hotkey so a preset
    // can't override the summon combo.
    for preset in presets {
        if preset.hotkey.trim().is_empty() {
            continue;
        }
        let parsed = match hotkey_parse::parse(&preset.hotkey) {
            Ok(sc) => sc,
            Err(e) => {
                warnings.push(format!(
                    "Invalid hotkey for '{}': {} ({})",
                    preset.name, preset.hotkey, e
                ));
                continue;
            }
        };
        let display = hotkey_parse::display(&preset.hotkey);
        if let Some(other) = seen_ids.get(&parsed.id()) {
            warnings.push(format!(
                "Duplicate hotkey {display}: '{}' collides with '{other}'",
                preset.name
            ));
            continue;
        }
        seen_ids.insert(parsed.id(), preset.name.clone());

        match shortcut_plugin.register(parsed) {
            Ok(()) => {
                if let Ok(mut map) = state.mapping.lock() {
                    map.insert(parsed.id(), preset.id.clone());
                }
            }
            Err(e) => {
                warnings.push(format!(
                    "Could not register {display} for '{}': {e}",
                    preset.name
                ));
            }
        }
    }
    warnings
}

/// Handler invoked by the plugin whenever any shortcut fires. Dispatches
/// to either the sidebar (summon) shortcut or a preset paste based on the
/// state registered in `HotkeyState`.
pub fn dispatch(app: &AppHandle, shortcut: &Shortcut, state: ShortcutState) {
    if state != ShortcutState::Pressed {
        return;
    }

    let hk_state = app.state::<HotkeyState>();
    if hk_state.is_sidebar(shortcut) {
        summon_window(app);
        return;
    }

    let Some(preset_id) = hk_state.preset_id_for(shortcut) else {
        return;
    };
    let app = app.clone();
    // `spawn_blocking` keeps the task tracked by the Tauri async runtime so
    // shutdown waits for it instead of leaking.
    async_runtime::spawn_blocking(move || {
        let presets = crate::storage::load_presets().unwrap_or_default();
        let Some(preset) = presets.into_iter().find(|p| p.id == preset_id) else {
            return;
        };
        if let Err(e) = crate::paste::paste_text(&app, &preset.text) {
            log::warn!("paste failed for preset {}: {e}", preset.name);
        }
    });
}

fn summon_window(app: &AppHandle) {
    if let Some(win) = app.get_webview_window(crate::MAIN_WINDOW) {
        let _ = win.show();
        let _ = win.unminimize();
        let _ = win.set_focus();
    }
}
