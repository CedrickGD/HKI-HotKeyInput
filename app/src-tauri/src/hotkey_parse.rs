//! Parse hotkey strings like `Ctrl+Shift+1`, `Alt+F`, `Ctrl+Space` into a
//! `tauri_plugin_global_shortcut::Shortcut`. Mirrors the tokens the Python
//! implementation accepts in `hki/windows_api.py::parse_hotkey`.

use tauri_plugin_global_shortcut::{Code, Modifiers, Shortcut};

#[derive(Debug)]
pub enum ParseError {
    Empty,
    NoKey,
    TooManyKeys,
    UnknownToken(String),
}

impl std::fmt::Display for ParseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ParseError::Empty => f.write_str("empty hotkey"),
            ParseError::NoKey => f.write_str("no key in hotkey"),
            ParseError::TooManyKeys => f.write_str("multiple non-modifier keys in hotkey"),
            ParseError::UnknownToken(t) => write!(f, "unknown token '{t}'"),
        }
    }
}
impl std::error::Error for ParseError {}

pub fn parse(value: &str) -> Result<Shortcut, ParseError> {
    let trimmed = value.trim();
    if trimmed.is_empty() {
        return Err(ParseError::Empty);
    }
    let mut mods = Modifiers::empty();
    let mut code: Option<Code> = None;

    for raw in trimmed.split('+') {
        let tok = raw.trim();
        if tok.is_empty() {
            continue;
        }
        let up = tok.to_ascii_uppercase();
        match up.as_str() {
            "CTRL" | "CONTROL" | "STRG" => {
                mods |= Modifiers::CONTROL;
                continue;
            }
            "ALT" => {
                mods |= Modifiers::ALT;
                continue;
            }
            "SHIFT" => {
                mods |= Modifiers::SHIFT;
                continue;
            }
            "WIN" | "META" | "SUPER" | "CMD" | "COMMAND" => {
                mods |= Modifiers::SUPER;
                continue;
            }
            _ => {}
        }
        let mapped = map_key(&up).ok_or_else(|| ParseError::UnknownToken(tok.to_string()))?;
        if code.is_some() {
            return Err(ParseError::TooManyKeys);
        }
        code = Some(mapped);
    }

    let Some(code) = code else {
        return Err(ParseError::NoKey);
    };
    Ok(Shortcut::new(Some(mods), code))
}

fn map_key(up: &str) -> Option<Code> {
    // single letter A..Z
    if up.len() == 1 {
        let c = up.chars().next()?;
        if c.is_ascii_alphabetic() {
            return match c {
                'A' => Some(Code::KeyA),
                'B' => Some(Code::KeyB),
                'C' => Some(Code::KeyC),
                'D' => Some(Code::KeyD),
                'E' => Some(Code::KeyE),
                'F' => Some(Code::KeyF),
                'G' => Some(Code::KeyG),
                'H' => Some(Code::KeyH),
                'I' => Some(Code::KeyI),
                'J' => Some(Code::KeyJ),
                'K' => Some(Code::KeyK),
                'L' => Some(Code::KeyL),
                'M' => Some(Code::KeyM),
                'N' => Some(Code::KeyN),
                'O' => Some(Code::KeyO),
                'P' => Some(Code::KeyP),
                'Q' => Some(Code::KeyQ),
                'R' => Some(Code::KeyR),
                'S' => Some(Code::KeyS),
                'T' => Some(Code::KeyT),
                'U' => Some(Code::KeyU),
                'V' => Some(Code::KeyV),
                'W' => Some(Code::KeyW),
                'X' => Some(Code::KeyX),
                'Y' => Some(Code::KeyY),
                'Z' => Some(Code::KeyZ),
                _ => None,
            };
        }
        if c.is_ascii_digit() {
            return match c {
                '0' => Some(Code::Digit0),
                '1' => Some(Code::Digit1),
                '2' => Some(Code::Digit2),
                '3' => Some(Code::Digit3),
                '4' => Some(Code::Digit4),
                '5' => Some(Code::Digit5),
                '6' => Some(Code::Digit6),
                '7' => Some(Code::Digit7),
                '8' => Some(Code::Digit8),
                '9' => Some(Code::Digit9),
                _ => None,
            };
        }
    }
    // F1..F24
    if let Some(rest) = up.strip_prefix('F') {
        if let Ok(n) = rest.parse::<u8>() {
            return match n {
                1 => Some(Code::F1),
                2 => Some(Code::F2),
                3 => Some(Code::F3),
                4 => Some(Code::F4),
                5 => Some(Code::F5),
                6 => Some(Code::F6),
                7 => Some(Code::F7),
                8 => Some(Code::F8),
                9 => Some(Code::F9),
                10 => Some(Code::F10),
                11 => Some(Code::F11),
                12 => Some(Code::F12),
                13 => Some(Code::F13),
                14 => Some(Code::F14),
                15 => Some(Code::F15),
                16 => Some(Code::F16),
                17 => Some(Code::F17),
                18 => Some(Code::F18),
                19 => Some(Code::F19),
                20 => Some(Code::F20),
                21 => Some(Code::F21),
                22 => Some(Code::F22),
                23 => Some(Code::F23),
                24 => Some(Code::F24),
                _ => None,
            };
        }
    }
    match up {
        "TAB" => Some(Code::Tab),
        "ENTER" | "RETURN" => Some(Code::Enter),
        "SPACE" => Some(Code::Space),
        "ESC" | "ESCAPE" => Some(Code::Escape),
        "UP" => Some(Code::ArrowUp),
        "DOWN" => Some(Code::ArrowDown),
        "LEFT" => Some(Code::ArrowLeft),
        "RIGHT" => Some(Code::ArrowRight),
        "INSERT" => Some(Code::Insert),
        "DELETE" | "DEL" => Some(Code::Delete),
        "HOME" => Some(Code::Home),
        "END" => Some(Code::End),
        "PAGEUP" | "PGUP" => Some(Code::PageUp),
        "PAGEDOWN" | "PGDN" => Some(Code::PageDown),
        "BACKSPACE" => Some(Code::Backspace),
        _ => None,
    }
}

/// Canonical, Ctrl/Alt/Shift-ordered display string for a hotkey value.
/// Falls back to the input (trimmed) if parsing fails.
pub fn display(value: &str) -> String {
    match parse(value) {
        Ok(sc) => format_shortcut(&sc),
        Err(_) => value.trim().to_string(),
    }
}

fn format_shortcut(sc: &Shortcut) -> String {
    let mut parts: Vec<&str> = Vec::new();
    if sc.mods.contains(Modifiers::CONTROL) {
        parts.push("Ctrl");
    }
    if sc.mods.contains(Modifiers::ALT) {
        parts.push("Alt");
    }
    if sc.mods.contains(Modifiers::SHIFT) {
        parts.push("Shift");
    }
    if sc.mods.contains(Modifiers::SUPER) {
        parts.push("Win");
    }
    let key = code_label(sc.key);
    parts.push(&key);
    parts.join("+")
}

fn code_label(code: Code) -> String {
    let dbg = format!("{code:?}");
    // Trim common prefixes so `KeyA` -> `A`, `Digit1` -> `1`, leave `F1`, named keys as-is.
    if let Some(rest) = dbg.strip_prefix("Key") {
        return rest.to_string();
    }
    if let Some(rest) = dbg.strip_prefix("Digit") {
        return rest.to_string();
    }
    match dbg.as_str() {
        "ArrowUp" => "Up".into(),
        "ArrowDown" => "Down".into(),
        "ArrowLeft" => "Left".into(),
        "ArrowRight" => "Right".into(),
        _ => dbg,
    }
}
