import {
  loadBackendSettings,
  saveBackendSettings,
  setAutostart as backendSetAutostart,
  type BackendSettings,
  type CustomPlaceholder,
} from "@/lib/backend";

export type Language = "en" | "de";

export type AppSettings = {
  autostart: boolean;
  closeToTray: boolean;
  minimizeToTray: boolean;
  language: Language;
  sidebarHotkey: string;
  dateFormat: string;
  timeFormat: string;
  customPlaceholders: CustomPlaceholder[];
};

const DEFAULTS: AppSettings = {
  autostart: false,
  closeToTray: true,
  minimizeToTray: false,
  language: "en",
  sidebarHotkey: "Ctrl+Shift+Space",
  dateFormat: "%d.%m.%Y",
  timeFormat: "%H:%M",
  customPlaceholders: [],
};

function normalizeCustomPlaceholders(
  raw: BackendSettings["customPlaceholders"] | undefined,
): CustomPlaceholder[] {
  if (!Array.isArray(raw)) return [];
  const out: CustomPlaceholder[] = [];
  for (const item of raw) {
    if (!item || typeof item !== "object") continue;
    const id = typeof item.id === "string" && item.id ? item.id : crypto.randomUUID();
    const key = typeof item.key === "string" ? item.key : "";
    const kind = item.kind === "datetime" ? "datetime" : "text";
    const value = typeof item.value === "string" ? item.value : "";
    out.push({ id, key, kind, value });
  }
  return out;
}

function normalize(raw: BackendSettings): AppSettings {
  const language: Language = raw.language === "de" ? "de" : "en";
  return {
    autostart: raw.autostart,
    closeToTray: raw.closeToTray,
    minimizeToTray: raw.minimizeToTray,
    language,
    sidebarHotkey: raw.sidebarHotkey || DEFAULTS.sidebarHotkey,
    dateFormat: raw.dateFormat && raw.dateFormat.length > 0 ? raw.dateFormat : DEFAULTS.dateFormat,
    timeFormat: raw.timeFormat && raw.timeFormat.length > 0 ? raw.timeFormat : DEFAULTS.timeFormat,
    customPlaceholders: normalizeCustomPlaceholders(raw.customPlaceholders),
  };
}

export async function loadSettings(): Promise<AppSettings> {
  try {
    const raw = await loadBackendSettings();
    return normalize(raw);
  } catch (err) {
    console.warn("[HKI] Failed to load settings:", err);
    return DEFAULTS;
  }
}

export async function saveSettings(settings: AppSettings): Promise<void> {
  try {
    await saveBackendSettings({
      autostart: settings.autostart,
      closeToTray: settings.closeToTray,
      minimizeToTray: settings.minimizeToTray,
      sidebarHotkey: settings.sidebarHotkey,
      language: settings.language,
      dateFormat: settings.dateFormat,
      timeFormat: settings.timeFormat,
      customPlaceholders: settings.customPlaceholders,
    });
  } catch (err) {
    console.warn("[HKI] Failed to save settings:", err);
  }
}

export async function setAutostart(enabled: boolean): Promise<void> {
  try {
    await backendSetAutostart(enabled);
  } catch (err) {
    console.warn("[HKI] Failed to toggle autostart:", err);
  }
}

export const DEFAULT_SETTINGS = DEFAULTS;
