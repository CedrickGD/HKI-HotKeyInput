//! System tray icon + context menu.
//!
//! Left-click toggles the main window; context menu has Show / Quit.

use anyhow::{Context, Result};
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Manager,
};

const MAIN_WINDOW: &str = "main";

pub fn build(app: &AppHandle) -> Result<()> {
    let show = MenuItem::with_id(app, "tray_show", "Show HKI", true, None::<&str>)
        .context("build tray 'Show' item")?;
    let quit = MenuItem::with_id(app, "tray_quit", "Quit", true, None::<&str>)
        .context("build tray 'Quit' item")?;
    let menu = Menu::with_items(app, &[&show, &quit]).context("build tray menu")?;

    let _tray = TrayIconBuilder::with_id("main")
        .icon(app.default_window_icon().cloned().context("default icon")?)
        .tooltip("HKI — HotKey Input")
        .menu(&menu)
        .show_menu_on_left_click(false)
        .on_menu_event(|app, event| match event.id.as_ref() {
            "tray_show" => show_main(app),
            "tray_quit" => app.exit(0),
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                toggle_main(tray.app_handle());
            }
        })
        .build(app)
        .context("build tray icon")?;
    Ok(())
}

pub fn show_main(app: &AppHandle) {
    if let Some(win) = app.get_webview_window(MAIN_WINDOW) {
        let _ = win.show();
        let _ = win.unminimize();
        let _ = win.set_focus();
    }
}

fn toggle_main(app: &AppHandle) {
    let Some(win) = app.get_webview_window(MAIN_WINDOW) else {
        return;
    };
    match win.is_visible() {
        Ok(true) => {
            let _ = win.hide();
        }
        _ => show_main(app),
    }
}
