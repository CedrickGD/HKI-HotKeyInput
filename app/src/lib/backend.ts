import { invoke } from "@tauri-apps/api/core";
import { open as openDialog, save as saveDialog } from "@tauri-apps/plugin-dialog";
import type { Preset } from "@/types";

const HKI_EXPORT_VERSION = "1.0.0";

type ExportFile = {
  hki_version: string;
  presets: Preset[];
};

export type CustomPlaceholderKind = "text" | "datetime";

export type CustomPlaceholder = {
  id: string;
  key: string;
  kind: CustomPlaceholderKind;
  value: string;
};

export type BackendSettings = {
  closeToTray: boolean;
  minimizeToTray: boolean;
  sidebarHotkey: string;
  autostart: boolean;
  language: string;
  dateFormat: string;
  timeFormat: string;
  customPlaceholders: CustomPlaceholder[];
};

export type TrashEntry = {
  preset: Preset;
  deletedAt: string;
};

declare global {
  interface Window {
    __TAURI_INTERNALS__?: unknown;
  }
}

export const isTauri: boolean =
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

const PRESETS_FALLBACK = "hki.presets.v1";
const SETTINGS_FALLBACK = "hki.settings.v1";
const TRASH_FALLBACK = "hki.trash.v1";

function readLocal<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeLocal<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (err) {
    console.warn(`[HKI] localStorage write failed for ${key}:`, err);
  }
}

export async function loadPresets(): Promise<Preset[]> {
  if (!isTauri) return readLocal<Preset[]>(PRESETS_FALLBACK, []);
  return invoke<Preset[]>("load_presets");
}

export async function savePresets(presets: Preset[]): Promise<void> {
  if (!isTauri) {
    writeLocal(PRESETS_FALLBACK, presets);
    return;
  }
  await invoke("save_presets", { presets });
}

export async function registerHotkeys(presets: Preset[]): Promise<string[]> {
  if (!isTauri) return [];
  return invoke<string[]>("register_hotkeys", { presets });
}

export async function pastePreset(presetId: string): Promise<void> {
  if (!isTauri) {
    console.warn("[HKI] paste_preset called outside Tauri runtime");
    return;
  }
  await invoke("paste_preset", { presetId });
}

export async function loadBackendSettings(): Promise<BackendSettings> {
  if (!isTauri) {
    return readLocal<BackendSettings>(SETTINGS_FALLBACK, {
      closeToTray: true,
      minimizeToTray: false,
      sidebarHotkey: "Ctrl+Shift+Space",
      autostart: false,
      language: "en",
      dateFormat: "%d.%m.%Y",
      timeFormat: "%H:%M",
      customPlaceholders: [],
    });
  }
  return invoke<BackendSettings>("load_settings");
}

export async function saveBackendSettings(
  settings: BackendSettings,
): Promise<void> {
  if (!isTauri) {
    writeLocal(SETTINGS_FALLBACK, settings);
    return;
  }
  await invoke("save_settings", { settings });
}

export async function setAutostart(enabled: boolean): Promise<void> {
  if (!isTauri) {
    const current = await loadBackendSettings();
    await saveBackendSettings({ ...current, autostart: enabled });
    return;
  }
  await invoke("set_autostart", { enabled });
}

/** Pass an empty string to open the HKI data directory. */
export async function openUrl(url = ""): Promise<void> {
  if (!isTauri) {
    if (url) window.open(url, "_blank", "noopener,noreferrer");
    return;
  }
  await invoke("open_url", { url });
}

/**
 * Prompts the user for a save path and writes the presets as an `.hki`
 * JSON file. Returns the picked path, or null if the user cancelled.
 */
export async function exportPresetsToFile(
  presets: Preset[],
): Promise<string | null> {
  if (!isTauri) {
    // Browser fallback — download via blob URL.
    const body: ExportFile = { hki_version: HKI_EXPORT_VERSION, presets };
    const blob = new Blob([JSON.stringify(body, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "presets.hki";
    a.click();
    URL.revokeObjectURL(url);
    return "presets.hki";
  }
  const path = await saveDialog({
    title: "Export presets",
    defaultPath: "presets.hki",
    filters: [{ name: "HKI presets", extensions: ["hki", "json"] }],
  });
  if (!path) return null;
  await invoke("export_presets_to_path", { path, presets });
  return path;
}

export async function isInstalled(): Promise<boolean> {
  if (!isTauri) return false;
  return invoke<boolean>("is_installed");
}

export async function installShortcut(): Promise<void> {
  if (!isTauri) return;
  await invoke("install_shortcut");
}

export async function uninstallShortcut(): Promise<void> {
  if (!isTauri) return;
  await invoke("uninstall_shortcut");
}

/** Removes shortcut + data dir and exits the app. Does not delete the exe. */
export async function uninstallApp(): Promise<void> {
  if (!isTauri) return;
  await invoke("uninstall_app");
}

/**
 * Prompts the user for an `.hki` file, parses it, and returns the presets
 * with fresh ids so imports can't clash with existing entries. Returns
 * null if the user cancelled.
 */
export async function importPresetsFromFile(): Promise<Preset[] | null> {
  if (!isTauri) {
    console.warn("[HKI] import_presets called outside Tauri runtime");
    return null;
  }
  const picked = await openDialog({
    title: "Import presets",
    multiple: false,
    filters: [{ name: "HKI presets", extensions: ["hki", "json"] }],
  });
  if (!picked || Array.isArray(picked)) return null;
  return invoke<Preset[]>("import_presets_from_path", { path: picked });
}

export async function getTrash(): Promise<TrashEntry[]> {
  if (!isTauri) return readLocal<TrashEntry[]>(TRASH_FALLBACK, []);
  return invoke<TrashEntry[]>("get_trash");
}

export async function trashPreset(preset: Preset): Promise<void> {
  if (!isTauri) {
    const list = readLocal<TrashEntry[]>(TRASH_FALLBACK, []);
    const next: TrashEntry[] = [
      { preset, deletedAt: new Date().toISOString() },
      ...list.filter((e) => e.preset.id !== preset.id),
    ];
    writeLocal(TRASH_FALLBACK, next);
    return;
  }
  await invoke("trash_preset", { preset });
}

export async function restoreFromTrash(id: string): Promise<Preset> {
  if (!isTauri) {
    const list = readLocal<TrashEntry[]>(TRASH_FALLBACK, []);
    const entry = list.find((e) => e.preset.id === id);
    if (!entry) {
      throw new Error(`No trashed preset with id ${id}`);
    }
    const next = list.filter((e) => e.preset.id !== id);
    writeLocal(TRASH_FALLBACK, next);
    return entry.preset;
  }
  return invoke<Preset>("restore_from_trash", { id });
}

export async function purgeFromTrash(id: string): Promise<void> {
  if (!isTauri) {
    const list = readLocal<TrashEntry[]>(TRASH_FALLBACK, []);
    writeLocal(
      TRASH_FALLBACK,
      list.filter((e) => e.preset.id !== id),
    );
    return;
  }
  await invoke("purge_from_trash", { id });
}

export async function emptyTrash(): Promise<void> {
  if (!isTauri) {
    writeLocal<TrashEntry[]>(TRASH_FALLBACK, []);
    return;
  }
  await invoke("empty_trash");
}
