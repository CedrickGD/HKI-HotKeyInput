import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Calendar,
  CheckCircle2,
  CircleDashed,
  Clock,
  FolderOpen,
  Plus,
  Power,
  RotateCcw,
  Settings as SettingsIcon,
  Trash2,
  Variable,
} from "lucide-react";
import { Dialog, DialogBody, DialogFooter, DialogHeader } from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { HotkeyInput } from "@/components/hotkey-input";
import {
  DEFAULT_SETTINGS,
  loadSettings,
  saveSettings,
  setAutostart,
  type AppSettings,
  type Language,
} from "@/lib/settings";
import {
  emptyTrash,
  getTrash,
  installShortcut,
  isInstalled,
  openUrl,
  purgeFromTrash,
  restoreFromTrash,
  uninstallApp,
  uninstallShortcut,
  type CustomPlaceholder,
  type CustomPlaceholderKind,
  type TrashEntry,
} from "@/lib/backend";
import { toast } from "@/lib/toast-store";
import { cn } from "@/lib/utils";
import { formatRelativeTime, formatStrftime } from "@/lib/strftime";
import type { Preset } from "@/types";

// Keep in sync with `app/src-tauri/tauri.conf.json`'s "version" field.
const APP_VERSION = "0.1.0";
const GITHUB_URL = "https://github.com/CedrickGD/HKI-HotKeyInput";

type SettingsDialogProps = {
  open: boolean;
  onClose: () => void;
  onRestorePreset: (preset: Preset) => void;
  /** Bumped by the parent whenever a preset is trashed so we re-fetch. */
  trashVersion: number;
};

const SETTINGS_SAVE_DEBOUNCE_MS = 300;
const PLACEHOLDER_KEY_INVALID = /[\s{}]/;

export function SettingsDialog({
  open,
  onClose,
  onRestorePreset,
  trashVersion,
}: SettingsDialogProps) {
  const [settings, setSettings] = React.useState<AppSettings>(DEFAULT_SETTINGS);
  const [installed, setInstalled] = React.useState<boolean | null>(null);
  const [installBusy, setInstallBusy] = React.useState(false);
  const [uninstallArmed, setUninstallArmed] = React.useState(false);
  const [trash, setTrash] = React.useState<TrashEntry[]>([]);
  const [emptyTrashArmed, setEmptyTrashArmed] = React.useState(false);
  const armedTimer = React.useRef<number | null>(null);
  const emptyTrashTimer = React.useRef<number | null>(null);
  // Debounce settings writes so fast typing in the strftime / placeholder
  // inputs doesn't hammer disk and trigger hotkey re-registration storms.
  const saveTimer = React.useRef<number | null>(null);
  const pendingSave = React.useRef<AppSettings | null>(null);
  // Kicks the relative-time strings ("2m ago") once a minute while the
  // dialog is open, so they don't go stale as the user reads them.
  const [, setNow] = React.useState(() => Date.now());

  React.useEffect(() => {
    if (!open) return;
    let cancelled = false;
    loadSettings().then((loaded) => {
      if (!cancelled) setSettings(loaded);
    });
    isInstalled()
      .then((v) => {
        if (!cancelled) setInstalled(v);
      })
      .catch(() => {
        if (!cancelled) setInstalled(false);
      });
    getTrash()
      .then((entries) => {
        if (!cancelled) setTrash(entries);
      })
      .catch((err: unknown) => {
        console.warn("[HKI] Failed to load trash:", err);
        if (!cancelled) setTrash([]);
      });
    const ticker = window.setInterval(() => setNow(Date.now()), 60_000);
    return () => {
      cancelled = true;
      window.clearInterval(ticker);
      if (armedTimer.current !== null) {
        window.clearTimeout(armedTimer.current);
        armedTimer.current = null;
      }
      if (emptyTrashTimer.current !== null) {
        window.clearTimeout(emptyTrashTimer.current);
        emptyTrashTimer.current = null;
      }
      // Flush any pending settings save so we don't drop a change when
      // the dialog closes mid-debounce.
      if (saveTimer.current !== null) {
        window.clearTimeout(saveTimer.current);
        saveTimer.current = null;
      }
      if (pendingSave.current) {
        void saveSettings(pendingSave.current);
        pendingSave.current = null;
      }
      setUninstallArmed(false);
      setEmptyTrashArmed(false);
    };
  }, [open]);

  // Live-refresh the trash list when the parent signals a delete while
  // this dialog is already open.
  React.useEffect(() => {
    if (!open) return;
    let cancelled = false;
    getTrash()
      .then((entries) => {
        if (!cancelled) setTrash(entries);
      })
      .catch(() => {
        /* handled on initial load */
      });
    return () => {
      cancelled = true;
    };
  }, [open, trashVersion]);

  const scheduleSave = React.useCallback((next: AppSettings) => {
    pendingSave.current = next;
    if (saveTimer.current !== null) {
      window.clearTimeout(saveTimer.current);
    }
    saveTimer.current = window.setTimeout(() => {
      if (pendingSave.current) {
        void saveSettings(pendingSave.current);
        pendingSave.current = null;
      }
      saveTimer.current = null;
    }, SETTINGS_SAVE_DEBOUNCE_MS);
  }, []);

  const update = React.useCallback(
    <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
      setSettings((prev) => {
        const next = { ...prev, [key]: value };
        scheduleSave(next);
        return next;
      });
    },
    [scheduleSave],
  );

  const handleAutostart = React.useCallback(
    (enabled: boolean) => {
      setSettings((prev) => ({ ...prev, autostart: enabled }));
      setAutostart(enabled)
        .then(() => {
          toast.success(
            enabled ? "Autostart enabled" : "Autostart disabled",
            enabled ? "HKI will launch with Windows." : undefined,
          );
        })
        .catch((err: unknown) => {
          const message = err instanceof Error ? err.message : String(err);
          toast.error("Autostart failed", message);
          setSettings((prev) => ({ ...prev, autostart: !enabled }));
        });
    },
    [],
  );

  const handleOpenFolder = React.useCallback(() => {
    openUrl("").catch((err: unknown) => {
      const message = err instanceof Error ? err.message : String(err);
      toast.error("Could not open folder", message);
    });
  }, []);

  const handleInstallToggle = React.useCallback(() => {
    if (installed === null || installBusy) return;
    setInstallBusy(true);
    const action = installed ? uninstallShortcut() : installShortcut();
    const wasInstalled = installed;
    action
      .then(() => {
        setInstalled(!wasInstalled);
        toast.success(
          wasInstalled ? "Removed from Start Menu" : "Added to Start Menu",
          wasInstalled
            ? undefined
            : "HKI is now searchable from Windows Search.",
        );
      })
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : String(err);
        toast.error(
          wasInstalled ? "Remove failed" : "Install failed",
          message,
        );
      })
      .finally(() => {
        setInstallBusy(false);
      });
  }, [installed, installBusy]);

  const handleUninstall = React.useCallback(() => {
    if (!uninstallArmed) {
      setUninstallArmed(true);
      if (armedTimer.current !== null) {
        window.clearTimeout(armedTimer.current);
      }
      armedTimer.current = window.setTimeout(() => {
        setUninstallArmed(false);
        armedTimer.current = null;
      }, 4000);
      return;
    }
    // Confirmed — fire uninstall. The Rust side exits the app after
    // removing the shortcut and data dir, so there's no UI to update.
    uninstallApp().catch((err: unknown) => {
      const message = err instanceof Error ? err.message : String(err);
      toast.error("Uninstall failed", message);
      setUninstallArmed(false);
    });
  }, [uninstallArmed]);

  const addCustomPlaceholder = React.useCallback(() => {
    const ph: CustomPlaceholder = {
      id: crypto.randomUUID(),
      key: "",
      kind: "text",
      value: "",
    };
    setSettings((prev) => {
      const next = { ...prev, customPlaceholders: [...prev.customPlaceholders, ph] };
      scheduleSave(next);
      return next;
    });
  }, [scheduleSave]);

  const updateCustomPlaceholder = React.useCallback(
    (id: string, patch: Partial<CustomPlaceholder>) => {
      // Reject invalid key characters (whitespace or braces) so tokens
      // stay parseable at paste time.
      const sanitised: Partial<CustomPlaceholder> =
        typeof patch.key === "string"
          ? { ...patch, key: patch.key.replace(PLACEHOLDER_KEY_INVALID, "") }
          : patch;
      setSettings((prev) => {
        const next = {
          ...prev,
          customPlaceholders: prev.customPlaceholders.map((p) =>
            p.id === id ? { ...p, ...sanitised } : p,
          ),
        };
        scheduleSave(next);
        return next;
      });
    },
    [scheduleSave],
  );

  const removeCustomPlaceholder = React.useCallback(
    (id: string) => {
      setSettings((prev) => {
        const next = {
          ...prev,
          customPlaceholders: prev.customPlaceholders.filter((p) => p.id !== id),
        };
        scheduleSave(next);
        return next;
      });
    },
    [scheduleSave],
  );

  const handleRestore = React.useCallback(
    (id: string) => {
      restoreFromTrash(id)
        .then((preset) => {
          setTrash((list) => list.filter((e) => e.preset.id !== id));
          onRestorePreset(preset);
          toast.success("Preset restored", preset.name || "Untitled preset");
        })
        .catch((err: unknown) => {
          const message = err instanceof Error ? err.message : String(err);
          toast.error("Restore failed", message);
        });
    },
    [onRestorePreset],
  );

  const handlePurge = React.useCallback((id: string) => {
    purgeFromTrash(id)
      .then(() => {
        setTrash((list) => list.filter((e) => e.preset.id !== id));
      })
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : String(err);
        toast.error("Purge failed", message);
      });
  }, []);

  const handleEmptyTrash = React.useCallback(() => {
    if (trash.length === 0) return;
    if (!emptyTrashArmed) {
      setEmptyTrashArmed(true);
      if (emptyTrashTimer.current !== null) {
        window.clearTimeout(emptyTrashTimer.current);
      }
      emptyTrashTimer.current = window.setTimeout(() => {
        setEmptyTrashArmed(false);
        emptyTrashTimer.current = null;
      }, 4000);
      return;
    }
    emptyTrash()
      .then(() => {
        setTrash([]);
        setEmptyTrashArmed(false);
        toast.success("Trash emptied");
      })
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : String(err);
        toast.error("Empty trash failed", message);
        setEmptyTrashArmed(false);
      });
  }, [emptyTrashArmed, trash.length]);

  const handleOpenGithub = React.useCallback(() => {
    openUrl(GITHUB_URL).catch((err: unknown) => {
      const message = err instanceof Error ? err.message : String(err);
      toast.error("Could not open browser", message);
    });
  }, []);

  return (
    <Dialog open={open} onClose={onClose} className="max-w-lg" label="Settings">
      <DialogHeader
        title="Settings"
        description="Customize how HKI behaves on your system."
        icon={<SettingsIcon className="h-4 w-4" />}
        onClose={onClose}
      />
      <DialogBody
        className="flex max-h-[80vh] flex-col gap-5 overflow-y-auto"
        tabIndex={-1}
      >
        <Row
          label="Start on login"
          description="Launch HKI automatically when Windows starts."
        >
          <Switch
            ariaLabel="Start on login"
            checked={settings.autostart}
            onCheckedChange={handleAutostart}
          />
        </Row>

        <Row
          label="Close to tray"
          description="Hide to the system tray instead of quitting."
        >
          <Switch
            ariaLabel="Close to tray"
            checked={settings.closeToTray}
            onCheckedChange={(v) => update("closeToTray", v)}
          />
        </Row>

        <Row
          label="Minimize to tray"
          description="Also hide when the window is minimized."
        >
          <Switch
            ariaLabel="Minimize to tray"
            checked={settings.minimizeToTray}
            onCheckedChange={(v) => update("minimizeToTray", v)}
          />
        </Row>

        <Row
          label="Language"
          description="Interface language for menus and labels."
        >
          <Select
            ariaLabel="Language"
            value={settings.language}
            onChange={(v) => update("language", v as Language)}
            options={[
              { value: "en", label: "English" },
              { value: "de", label: "Deutsch" },
            ]}
            className="w-40"
          />
        </Row>

        <Row
          label="Summon hotkey"
          description="Global shortcut that brings the HKI window to the front."
          align="start"
        >
          <div className="w-full max-w-[260px]">
            <HotkeyInput
              value={settings.sidebarHotkey}
              onChange={(v) => update("sidebarHotkey", v)}
            />
          </div>
        </Row>

        <FormatsSection
          dateFormat={settings.dateFormat}
          timeFormat={settings.timeFormat}
          onDateFormatChange={(v) => update("dateFormat", v)}
          onTimeFormatChange={(v) => update("timeFormat", v)}
        />

        <CustomPlaceholdersSection
          placeholders={settings.customPlaceholders}
          onAdd={addCustomPlaceholder}
          onUpdate={updateCustomPlaceholder}
          onRemove={removeCustomPlaceholder}
        />

        <TrashSection
          trash={trash}
          emptyArmed={emptyTrashArmed}
          onEmpty={handleEmptyTrash}
          onRestore={handleRestore}
          onPurge={handlePurge}
        />

        <div className="border-t border-border/60 pt-4">
          <Button variant="outline" size="sm" onClick={handleOpenFolder}>
            <FolderOpen className="h-3.5 w-3.5" />
            Open settings folder
          </Button>
        </div>

        <div className="flex flex-col gap-3 border-t border-border/60 pt-4">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                {installed ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    <span>Installed to Start Menu</span>
                  </>
                ) : installed === null ? (
                  <>
                    <CircleDashed className="h-4 w-4 text-muted-foreground" />
                    <span>Checking…</span>
                  </>
                ) : (
                  <>
                    <CircleDashed className="h-4 w-4 text-muted-foreground" />
                    <span>Portable mode</span>
                  </>
                )}
              </div>
              <div className="mt-0.5 text-xs text-muted-foreground">
                {installed
                  ? "HKI is searchable from Windows Search. The shortcut points to the exe's current folder."
                  : "Add a Start Menu shortcut so you can launch HKI from Windows Search."}
              </div>
            </div>
            <Button
              variant={installed ? "ghost" : "outline"}
              size="sm"
              onClick={handleInstallToggle}
              disabled={installed === null || installBusy}
              className="shrink-0"
            >
              <Power className="h-3.5 w-3.5" />
              {installed ? "Remove shortcut" : "Add to Start Menu"}
            </Button>
          </div>

          <div className="flex items-start justify-between gap-4 rounded-md border border-destructive/20 bg-destructive/5 p-3">
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium text-foreground">
                Uninstall HKI
              </div>
              <div className="mt-0.5 text-xs text-muted-foreground">
                Removes the Start Menu shortcut and all settings + presets in{" "}
                <code className="font-mono text-[10px] text-foreground">
                  %LOCALAPPDATA%\HKI
                </code>
                , then quits. The <code className="font-mono text-[10px] text-foreground">HKI.exe</code> file is left in place — delete it manually.
              </div>
            </div>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleUninstall}
              className={cn("shrink-0", uninstallArmed && "animate-pulse")}
            >
              <Trash2 className="h-3.5 w-3.5" />
              {uninstallArmed ? "Click again to confirm" : "Uninstall"}
            </Button>
          </div>
        </div>

        <AboutSection onOpenGithub={handleOpenGithub} />
      </DialogBody>
      <DialogFooter>
        <Button variant="ghost" size="sm" onClick={onClose}>
          Close
        </Button>
      </DialogFooter>
    </Dialog>
  );
}

function SectionHeader({
  icon,
  title,
  description,
  trailing,
}: {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  trailing?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-3 border-t border-border/60 pt-4">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
          {icon}
          <span>{title}</span>
        </div>
        {description ? (
          <div className="mt-0.5 text-xs text-muted-foreground">{description}</div>
        ) : null}
      </div>
      {trailing ? <div className="shrink-0">{trailing}</div> : null}
    </div>
  );
}

function FormatsSection({
  dateFormat,
  timeFormat,
  onDateFormatChange,
  onTimeFormatChange,
}: {
  dateFormat: string;
  timeFormat: string;
  onDateFormatChange: (v: string) => void;
  onTimeFormatChange: (v: string) => void;
}) {
  const [now, setNow] = React.useState(() => new Date());

  React.useEffect(() => {
    const handle = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(handle);
  }, []);

  const datePreview = React.useMemo(
    () => formatStrftime(dateFormat, now),
    [dateFormat, now],
  );
  const timePreview = React.useMemo(
    () => formatStrftime(timeFormat, now),
    [timeFormat, now],
  );

  return (
    <div className="flex flex-col gap-3">
      <SectionHeader
        icon={<Calendar className="h-4 w-4 text-primary" />}
        title="Formats"
        description="Control how {date} and {time} render in pasted text."
      />
      <div className="flex flex-col gap-1.5">
        <label className="flex items-center gap-2 text-xs font-medium text-muted-foreground" htmlFor="hki-date-format">
          <Calendar className="h-3.5 w-3.5" />
          Date format
        </label>
        <Input
          id="hki-date-format"
          value={dateFormat}
          onChange={(e) => onDateFormatChange(e.target.value)}
          placeholder="%d.%m.%Y"
          aria-label="Date format pattern"
          className="font-mono text-sm"
        />
        <div className="text-[11px] text-muted-foreground">
          Today: <span className="font-mono text-foreground">{datePreview}</span>
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <label className="flex items-center gap-2 text-xs font-medium text-muted-foreground" htmlFor="hki-time-format">
          <Clock className="h-3.5 w-3.5" />
          Time format
        </label>
        <Input
          id="hki-time-format"
          value={timeFormat}
          onChange={(e) => onTimeFormatChange(e.target.value)}
          placeholder="%H:%M"
          aria-label="Time format pattern"
          className="font-mono text-sm"
        />
        <div className="text-[11px] text-muted-foreground">
          Now: <span className="font-mono text-foreground">{timePreview}</span>
        </div>
      </div>
    </div>
  );
}

function CustomPlaceholdersSection({
  placeholders,
  onAdd,
  onUpdate,
  onRemove,
}: {
  placeholders: CustomPlaceholder[];
  onAdd: () => void;
  onUpdate: (id: string, patch: Partial<CustomPlaceholder>) => void;
  onRemove: (id: string) => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      <SectionHeader
        icon={<Variable className="h-4 w-4 text-primary" />}
        title="Custom placeholders"
        trailing={
          <Button
            variant="outline"
            size="sm"
            onClick={onAdd}
            aria-label="Add custom placeholder"
          >
            <Plus className="h-3.5 w-3.5" />
            Add placeholder
          </Button>
        }
      />
      <p className="text-xs text-muted-foreground">
        Use these tokens in your preset text (e.g.{" "}
        <code className="font-mono text-[11px] text-foreground">{"{signature}"}</code>
        ). Built-in tokens:{" "}
        <code className="font-mono text-[11px] text-foreground">{"{date}"}</code>,{" "}
        <code className="font-mono text-[11px] text-foreground">{"{time}"}</code>.
      </p>
      <div className="flex flex-col gap-2">
        <AnimatePresence initial={false}>
          {placeholders.map((p) => (
            <motion.div
              key={p.id}
              layout
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ type: "spring", stiffness: 360, damping: 30 }}
              className="flex flex-col gap-2 rounded-md border border-border/60 bg-muted/20 p-2 sm:flex-row sm:items-center"
            >
              <div className="relative sm:w-32">
                <span className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 font-mono text-xs text-muted-foreground">
                  {"{"}
                </span>
                <Input
                  value={p.key}
                  onChange={(e) => onUpdate(p.id, { key: e.target.value })}
                  placeholder="key"
                  aria-label="Placeholder key"
                  className="pl-6 pr-5 font-mono text-sm"
                />
                <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 font-mono text-xs text-muted-foreground">
                  {"}"}
                </span>
              </div>
              <Select
                ariaLabel="Placeholder kind"
                value={p.kind}
                onChange={(v) =>
                  onUpdate(p.id, { kind: v as CustomPlaceholderKind })
                }
                options={[
                  { value: "text", label: "Text" },
                  { value: "datetime", label: "Date-time" },
                ]}
                className="sm:w-32"
              />
              <Input
                value={p.value}
                onChange={(e) => onUpdate(p.id, { value: e.target.value })}
                placeholder={
                  p.kind === "datetime"
                    ? "e.g. %A, %d %B %Y"
                    : "Verbatim text"
                }
                aria-label="Placeholder value"
                className={cn(
                  "flex-1",
                  p.kind === "datetime" && "font-mono text-sm",
                )}
              />
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onRemove(p.id)}
                aria-label="Remove placeholder"
                className="shrink-0"
              >
                <Trash2 className="h-4 w-4 text-muted-foreground" />
              </Button>
            </motion.div>
          ))}
        </AnimatePresence>
        {placeholders.length === 0 ? (
          <p className="py-2 text-center text-xs text-muted-foreground">
            No custom placeholders yet.
          </p>
        ) : null}
      </div>
    </div>
  );
}

function TrashSection({
  trash,
  emptyArmed,
  onEmpty,
  onRestore,
  onPurge,
}: {
  trash: TrashEntry[];
  emptyArmed: boolean;
  onEmpty: () => void;
  onRestore: (id: string) => void;
  onPurge: (id: string) => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      <SectionHeader
        icon={<Trash2 className="h-4 w-4 text-primary" />}
        title="Recently deleted"
        description="Restore deleted presets or remove them permanently."
        trailing={
          <Button
            variant="destructive"
            size="sm"
            onClick={onEmpty}
            disabled={trash.length === 0}
            className={cn(emptyArmed && "animate-pulse")}
            aria-label="Empty trash"
          >
            <Trash2 className="h-3.5 w-3.5" />
            {emptyArmed ? "Click again" : "Empty trash"}
          </Button>
        }
      />
      <div className="flex flex-col gap-1.5">
        <AnimatePresence initial={false}>
          {trash.map((entry) => (
            <motion.div
              key={entry.preset.id}
              layout
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ type: "spring", stiffness: 360, damping: 30 }}
              className="flex items-center gap-2 rounded-md border border-border/60 bg-muted/20 px-3 py-2"
            >
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium text-foreground">
                  {entry.preset.name || "Untitled preset"}
                </div>
                <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                  {entry.preset.hotkey ? (
                    <code className="font-mono">{entry.preset.hotkey}</code>
                  ) : (
                    <span>No hotkey</span>
                  )}
                  <span aria-hidden="true">·</span>
                  <span>{formatRelativeTime(entry.deletedAt)}</span>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onRestore(entry.preset.id)}
                aria-label={`Restore ${entry.preset.name || "preset"}`}
                className="shrink-0"
              >
                <RotateCcw className="h-4 w-4 text-primary" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onPurge(entry.preset.id)}
                aria-label={`Permanently delete ${entry.preset.name || "preset"}`}
                className="shrink-0"
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </motion.div>
          ))}
        </AnimatePresence>
        {trash.length === 0 ? (
          <p className="py-2 text-center text-xs text-muted-foreground">
            No recently deleted presets.
          </p>
        ) : null}
      </div>
    </div>
  );
}

function AboutSection({ onOpenGithub }: { onOpenGithub: () => void }) {
  return (
    <div className="flex items-center justify-between gap-4 border-t border-border/60 pt-4">
      <div className="flex items-center gap-3">
        <img
          src="/hki-logo.png"
          alt=""
          aria-hidden="true"
          width={22}
          height={22}
          className="h-[22px] w-[22px] rounded-sm"
        />
        <div>
          <div className="text-sm font-medium text-foreground">
            HKI — HotKey Input
          </div>
          <div className="text-[11px] text-muted-foreground">
            v{APP_VERSION} · by Cedrick Grabe
          </div>
        </div>
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={onOpenGithub}
        aria-label="Open GitHub repository"
      >
        <GithubIcon className="h-3.5 w-3.5" />
        GitHub
      </Button>
    </div>
  );
}

function GithubIcon({ className }: { className?: string }) {
  // lucide-react@1.8 doesn't ship the Github mark; inline the official
  // octocat glyph so we match the visual the design asks for.
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
      className={className}
    >
      <path d="M12 .5C5.73.5.5 5.73.5 12.07c0 5.11 3.29 9.44 7.86 10.97.57.1.78-.25.78-.55v-2.11c-3.2.7-3.87-1.38-3.87-1.38-.52-1.34-1.27-1.7-1.27-1.7-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.2 1.76 1.2 1.02 1.78 2.68 1.26 3.34.96.1-.74.4-1.26.72-1.55-2.55-.29-5.24-1.29-5.24-5.72 0-1.27.45-2.3 1.19-3.11-.12-.3-.52-1.47.11-3.07 0 0 .97-.31 3.19 1.18a11 11 0 0 1 5.8 0c2.22-1.5 3.19-1.18 3.19-1.18.63 1.6.23 2.77.11 3.07.74.81 1.19 1.84 1.19 3.11 0 4.44-2.69 5.42-5.26 5.71.41.35.78 1.05.78 2.12v3.14c0 .3.21.66.79.55 4.57-1.53 7.86-5.86 7.86-10.97C23.5 5.73 18.27.5 12 .5Z" />
    </svg>
  );
}

function Row({
  label,
  description,
  children,
  align = "center",
}: {
  label: string;
  description?: string;
  children: React.ReactNode;
  align?: "start" | "center";
}) {
  return (
    <div
      className={`flex ${
        align === "start" ? "items-start" : "items-center"
      } justify-between gap-4`}
    >
      <div className="min-w-0 flex-1">
        <div className="text-sm font-medium text-foreground">{label}</div>
        {description ? (
          <div className="mt-0.5 text-xs text-muted-foreground">{description}</div>
        ) : null}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}
