//! Native backend for HKI-HotKeyInput.
//!
//! Registers the Tauri v2 plugins, exposes commands to the React frontend,
//! and wires up the global hotkey registry, tray, and paste pipeline.

mod commands;
mod hotkey_parse;
mod hotkeys;
mod paste;
mod placeholders;
mod storage;
mod trash;
mod tray;

use tauri::{Manager, RunEvent, WindowEvent};
use tauri_plugin_autostart::MacosLauncher;
use tauri_plugin_global_shortcut::GlobalShortcutExt;

use crate::hotkeys::HotkeyState;

pub const MAIN_WINDOW: &str = "main";

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default();

    #[cfg(desktop)]
    {
        builder = builder.plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(win) = app.get_webview_window(MAIN_WINDOW) {
                let _ = win.show();
                let _ = win.unminimize();
                let _ = win.set_focus();
            }
        }));
    }

    builder = builder
        .plugin(
            tauri_plugin_global_shortcut::Builder::new()
                .with_handler(|app, shortcut, event| {
                    hotkeys::dispatch(app, shortcut, event.state());
                })
                .build(),
        )
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_autostart::init(
            MacosLauncher::LaunchAgent,
            None,
        ))
        .manage(HotkeyState::new())
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            tray::build(app.handle())?;

            let handle = app.handle().clone();
            // Register hotkeys for whatever presets are on disk at startup,
            // plus the summon sidebar hotkey from settings.
            let presets = storage::load_presets().unwrap_or_default();
            let settings = storage::load_settings().unwrap_or_default();
            let warnings = hotkeys::register_all(&handle, &presets, &settings.sidebar_hotkey);
            for w in warnings {
                log::warn!("hotkey: {w}");
            }

            // Garbage-collect old trash entries once on startup so stale
            // deletes don't accumulate forever.
            match trash::purge_older_than(30) {
                Ok(0) => {}
                Ok(n) => log::info!(
                    "trash: purged {n} entr{} older than 30 days",
                    if n == 1 { "y" } else { "ies" }
                ),
                Err(e) => log::warn!("trash purge failed: {e:#}"),
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            if window.label() != MAIN_WINDOW {
                return;
            }
            match event {
                WindowEvent::CloseRequested { api, .. } => {
                    let settings = storage::load_settings().unwrap_or_default();
                    if settings.close_to_tray {
                        api.prevent_close();
                        let _ = window.hide();
                    }
                }
                WindowEvent::Resized(_) => {
                    // Tauri v2 doesn't surface a dedicated "Minimized"
                    // event on Windows; resize fires when minimize toggles
                    // the window state.
                    if let Ok(true) = window.is_minimized() {
                        let settings = storage::load_settings().unwrap_or_default();
                        if settings.minimize_to_tray {
                            let _ = window.hide();
                        }
                    }
                }
                _ => {}
            }
        })
        .invoke_handler(tauri::generate_handler![
            commands::load_presets,
            commands::save_presets,
            commands::register_hotkeys,
            commands::paste_preset,
            commands::load_settings,
            commands::save_settings,
            commands::set_autostart,
            commands::open_url,
            commands::export_presets_to_path,
            commands::import_presets_from_path,
            commands::is_installed,
            commands::install_shortcut,
            commands::uninstall_shortcut,
            commands::uninstall_app,
            commands::get_trash,
            commands::trash_preset,
            commands::restore_from_trash,
            commands::purge_from_trash,
            commands::empty_trash,
        ]);

    let app = builder
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| {
        if let RunEvent::ExitRequested { .. } = event {
            // Make sure global hotkeys are removed on real exit.
            let _ = app_handle.global_shortcut().unregister_all();
        }
    });
}
