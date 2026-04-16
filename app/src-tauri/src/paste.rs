//! Clipboard-based paste simulation.
//!
//! Mirrors `hki/windows_api.py::send_ctrl_v`: set the clipboard to the
//! resolved preset text, synthesise Ctrl+V via `SendInput`, restore the
//! previous clipboard after a short delay.

use std::time::Duration;

use anyhow::{Context, Result};
use tauri::async_runtime;
use tauri::AppHandle;
use tauri_plugin_clipboard_manager::ClipboardExt;

use windows::Win32::UI::Input::KeyboardAndMouse::{
    SendInput, INPUT, INPUT_0, INPUT_KEYBOARD, KEYBDINPUT, KEYBD_EVENT_FLAGS, KEYEVENTF_KEYUP,
    VIRTUAL_KEY, VK_CONTROL, VK_V,
};

const RESTORE_DELAY: Duration = Duration::from_millis(150);
/// Short gap between setting the clipboard and pressing Ctrl+V. Gives the
/// target app's message loop a chance to see the clipboard update before
/// we inject the key sequence.
const PRE_SEND_DELAY: Duration = Duration::from_millis(40);

/// Resolve the placeholders, set the clipboard, synthesise Ctrl+V, then
/// restore the previous clipboard on a background task.
///
/// The clipboard is always restored even if the `SendInput` call fails —
/// otherwise a failed paste would leave the user's clipboard clobbered
/// with the preset text.
pub fn paste_text(app: &AppHandle, text: &str) -> Result<()> {
    let settings = crate::storage::load_settings().unwrap_or_default();
    let resolved = crate::placeholders::resolve(text, &settings);
    let clipboard = app.clipboard();
    let previous = clipboard.read_text().ok();

    clipboard
        .write_text(resolved)
        .context("write clipboard text")?;

    // Schedule the restore before we attempt SendInput so a failing paste
    // still gives the user their original clipboard back.
    let app_clone = app.clone();
    async_runtime::spawn_blocking(move || {
        std::thread::sleep(RESTORE_DELAY);
        if let Some(prev) = previous {
            let _ = app_clone.clipboard().write_text(prev);
        }
    });

    std::thread::sleep(PRE_SEND_DELAY);
    send_ctrl_v().context("SendInput Ctrl+V")?;
    Ok(())
}

fn send_ctrl_v() -> Result<()> {
    let inputs = [
        key_input(VK_CONTROL, KEYBD_EVENT_FLAGS(0)),
        key_input(VK_V, KEYBD_EVENT_FLAGS(0)),
        key_input(VK_V, KEYEVENTF_KEYUP),
        key_input(VK_CONTROL, KEYEVENTF_KEYUP),
    ];
    let sent = unsafe { SendInput(&inputs, std::mem::size_of::<INPUT>() as i32) };
    if sent as usize != inputs.len() {
        anyhow::bail!("SendInput sent {} of {} events", sent, inputs.len());
    }
    Ok(())
}

fn key_input(vk: VIRTUAL_KEY, flags: KEYBD_EVENT_FLAGS) -> INPUT {
    INPUT {
        r#type: INPUT_KEYBOARD,
        Anonymous: INPUT_0 {
            ki: KEYBDINPUT {
                wVk: vk,
                wScan: 0,
                dwFlags: flags,
                time: 0,
                dwExtraInfo: 0,
            },
        },
    }
}
