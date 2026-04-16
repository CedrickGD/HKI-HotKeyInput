//! Built-in placeholder resolution ported from `hki/clipboard.py`.
//!
//! Supports the built-in `{date}` / `{time}` tokens plus any user-defined
//! `AppSettings::custom_placeholders` entries. Custom placeholder
//! metadata carried by a single preset is intentionally ignored here —
//! those are user-prompt fields handled by the frontend.

use std::panic;

use chrono::{DateTime, Local};

use crate::storage::AppSettings;

const DEFAULT_DATE_FORMAT: &str = "%d.%m.%Y";
const DEFAULT_TIME_FORMAT: &str = "%H:%M";

/// Replace every recognised token in `text`.
///
/// Built-in `{date}` and `{time}` win over any custom placeholder sharing
/// their key. A broken user-supplied strftime pattern never panics — the
/// token is either swapped for the default format (for the built-ins) or
/// left untouched (for custom ones), and a warning is logged.
pub fn resolve(text: &str, settings: &AppSettings) -> String {
    let now = Local::now();

    let mut out = text.to_string();

    if out.contains("{date}") {
        let date = format_local(&now, &settings.date_format).unwrap_or_else(|| {
            log::warn!(
                "invalid dateFormat '{}', falling back to '{DEFAULT_DATE_FORMAT}'",
                settings.date_format
            );
            format_local(&now, DEFAULT_DATE_FORMAT).unwrap_or_default()
        });
        out = out.replace("{date}", &date);
    }

    if out.contains("{time}") {
        let time = format_local(&now, &settings.time_format).unwrap_or_else(|| {
            log::warn!(
                "invalid timeFormat '{}', falling back to '{DEFAULT_TIME_FORMAT}'",
                settings.time_format
            );
            format_local(&now, DEFAULT_TIME_FORMAT).unwrap_or_default()
        });
        out = out.replace("{time}", &time);
    }

    for placeholder in &settings.custom_placeholders {
        if placeholder.key.is_empty() {
            continue;
        }
        // Built-ins win — skip any user custom that would shadow them.
        if placeholder.key == "date" || placeholder.key == "time" {
            continue;
        }
        let token = format!("{{{}}}", placeholder.key);
        if !out.contains(&token) {
            continue;
        }
        match placeholder.kind.as_str() {
            "datetime" => match format_local(&now, &placeholder.value) {
                Some(formatted) => {
                    out = out.replace(&token, &formatted);
                }
                None => {
                    log::warn!(
                        "invalid datetime pattern '{}' for placeholder '{{{}}}'; leaving token in place",
                        placeholder.value,
                        placeholder.key
                    );
                }
            },
            _ => {
                // "text" (and any forward-compatible unknown) — verbatim.
                out = out.replace(&token, &placeholder.value);
            }
        }
    }

    out
}

/// Format `now` with `fmt` as strftime, returning `None` on any error or
/// panic so callers can fall back cleanly.
fn format_local(now: &DateTime<Local>, fmt: &str) -> Option<String> {
    // chrono::format::DelayedFormat is lazy — the pattern isn't actually
    // validated until we render it, and bad specifiers can panic in the
    // Display impl. Catch that so malformed user input never crashes a
    // paste.
    let now = *now;
    let fmt = fmt.to_string();
    let result = panic::catch_unwind(move || {
        use std::fmt::Write;
        let mut buf = String::new();
        write!(&mut buf, "{}", now.format(&fmt)).map(|_| buf)
    });
    match result {
        Ok(Ok(s)) => Some(s),
        _ => None,
    }
}
