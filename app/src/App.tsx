import * as React from "react";
import { AnimatePresence } from "framer-motion";
import { Sparkles } from "lucide-react";
import { TitleBar } from "@/components/title-bar";
import { PresetList } from "@/components/preset-list";
import { PresetEditor } from "@/components/preset-editor";
import { StatusBar } from "@/components/status-bar";
import { Toaster } from "@/components/toaster";
import { EmptyState } from "@/components/empty-state";

const SettingsDialog = React.lazy(() =>
  import("@/components/settings-dialog").then((m) => ({ default: m.SettingsDialog })),
);
const CommandPalette = React.lazy(() =>
  import("@/components/command-palette").then((m) => ({ default: m.CommandPalette })),
);
import { toast } from "@/lib/toast-store";
import {
  exportPresetsToFile,
  importPresetsFromFile,
  isTauri,
  loadPresets as backendLoadPresets,
  pastePreset,
  registerHotkeys,
  restoreFromTrash,
  savePresets,
  trashPreset,
} from "@/lib/backend";
import { useResizable } from "@/lib/use-resizable";
import { cn } from "@/lib/utils";
import type { Preset } from "@/types";

const SEED_PRESETS: Preset[] = [
  {
    id: crypto.randomUUID(),
    name: "Friendly greeting",
    hotkey: "Ctrl+Shift+1",
    text: "Hi {name}, hope you're having a great day!",
    placeholders: [
      { id: crypto.randomUUID(), key: "name", label: "Recipient name" },
    ],
  },
  {
    id: crypto.randomUUID(),
    name: "Email signature",
    hotkey: "Ctrl+Shift+2",
    text: "Best regards,\nCedrick",
    placeholders: [],
  },
  {
    id: crypto.randomUUID(),
    name: "Meeting follow-up",
    hotkey: "",
    text: "Thanks for the chat today. Next steps: {steps}",
    placeholders: [
      { id: crypto.randomUUID(), key: "steps", label: "Next steps" },
    ],
  },
  {
    id: crypto.randomUUID(),
    name: "Sign & date",
    hotkey: "",
    text: "— Cedrick, {date}",
    placeholders: [],
  },
  {
    id: crypto.randomUUID(),
    name: "Time-stamped note",
    hotkey: "",
    text: "[{time}] ",
    placeholders: [],
  },
];

function computeConflicts(presets: Preset[]): Set<string> {
  const counts = new Map<string, number>();
  for (const p of presets) {
    const h = p.hotkey.trim();
    if (!h) continue;
    counts.set(h, (counts.get(h) ?? 0) + 1);
  }
  const conflicts = new Set<string>();
  for (const p of presets) {
    const h = p.hotkey.trim();
    if (h && (counts.get(h) ?? 0) > 1) conflicts.add(p.id);
  }
  return conflicts;
}

function hotkeySignature(presets: Preset[]): string {
  return presets.map((p) => `${p.id}::${p.hotkey}`).join("|");
}

const SAVE_DEBOUNCE_MS = 250;

export default function App() {
  const [presets, setPresets] = React.useState<Preset[]>([]);
  const [activeId, setActiveId] = React.useState<string | null>(null);
  const [query, setQuery] = React.useState("");
  const [settingsOpen, setSettingsOpen] = React.useState(false);
  const [paletteOpen, setPaletteOpen] = React.useState(false);
  const [loaded, setLoaded] = React.useState(false);
  const [trashVersion, setTrashVersion] = React.useState(0);
  const searchRef = React.useRef<HTMLInputElement>(null);
  const lastHotkeySig = React.useRef<string>("");
  const sidebar = useResizable({
    storageKey: "hki.sidebar.width",
    defaultWidth: 300,
    min: 220,
    max: 520,
  });

  // Initial load from backend (or localStorage fallback). Seeds defaults on
  // first run so the user isn't staring at an empty list.
  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const fromDisk = await backendLoadPresets();
        if (cancelled) return;
        if (fromDisk.length > 0) {
          setPresets(fromDisk);
          setActiveId(fromDisk[0]?.id ?? null);
          // Rust's startup handler already registered the on-disk
          // hotkeys — mark them in sync so the save effect doesn't
          // redundantly re-register.
          lastHotkeySig.current = hotkeySignature(fromDisk);
        } else {
          setPresets(SEED_PRESETS);
          setActiveId(SEED_PRESETS[0]?.id ?? null);
          void savePresets(SEED_PRESETS);
          // Leave lastHotkeySig empty so the first save effect fires
          // registerHotkeys for the seeds — Rust had nothing on disk
          // at startup so nothing is registered yet.
          lastHotkeySig.current = "";
        }
      } catch (err) {
        console.warn("[HKI] Failed to load presets:", err);
        setPresets(SEED_PRESETS);
        setActiveId(SEED_PRESETS[0]?.id ?? null);
      } finally {
        if (!cancelled) setLoaded(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Persist + re-register hotkeys whenever presets change. Debounced so we
  // don't hammer disk on every keystroke in the editor. `cancelled` guards
  // the async chain so an unmount (or a superseding edit) doesn't fire a
  // late toast or race the next save.
  React.useEffect(() => {
    if (!loaded) return;
    let cancelled = false;
    const handle = window.setTimeout(() => {
      void (async () => {
        try {
          await savePresets(presets);
          if (cancelled) return;
          const nextSig = hotkeySignature(presets);
          if (nextSig !== lastHotkeySig.current) {
            lastHotkeySig.current = nextSig;
            const warnings = await registerHotkeys(presets);
            if (cancelled) return;
            for (const w of warnings) {
              toast.info("Hotkey warning", w);
            }
          }
        } catch (err) {
          if (cancelled) return;
          const msg = err instanceof Error ? err.message : String(err);
          toast.error("Could not save presets", msg);
        }
      })();
    }, SAVE_DEBOUNCE_MS);
    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
  }, [presets, loaded]);

  const active = presets.find((p) => p.id === activeId) ?? null;
  const conflicts = React.useMemo(() => computeConflicts(presets), [presets]);
  const hotkeyCount = React.useMemo(
    () => presets.filter((p) => p.hotkey.trim().length > 0).length,
    [presets],
  );

  const handleCreate = React.useCallback(() => {
    const p: Preset = {
      id: crypto.randomUUID(),
      name: "",
      hotkey: "",
      text: "",
      placeholders: [],
    };
    setPresets((list) => [p, ...list]);
    setActiveId(p.id);
    toast.success("Preset created", "Name it and bind a hotkey.");
  }, []);

  const handleChange = React.useCallback((p: Preset) => {
    setPresets((list) => list.map((x) => (x.id === p.id ? p : x)));
  }, []);

  const handleDuplicate = React.useCallback(() => {
    setPresets((list) => {
      const current = list.find((p) => p.id === activeId);
      if (!current) return list;
      const dup: Preset = {
        ...current,
        id: crypto.randomUUID(),
        name: current.name ? `${current.name} (copy)` : "",
        hotkey: "",
        placeholders: current.placeholders.map((ph) => ({
          ...ph,
          id: crypto.randomUUID(),
        })),
      };
      setActiveId(dup.id);
      toast.success("Preset duplicated");
      return [dup, ...list];
    });
  }, [activeId]);

  const handleRestorePreset = React.useCallback((preset: Preset) => {
    setPresets((list) => {
      if (list.some((p) => p.id === preset.id)) return list;
      const next = [preset, ...list];
      // Persist immediately rather than waiting for the 250ms debounce
      // so a rapid force-quit can't lose the restored preset during the
      // window where trash.json has already removed the entry but
      // presets.json hasn't been rewritten yet.
      void savePresets(next);
      return next;
    });
    setActiveId(preset.id);
  }, []);

  const handleDelete = React.useCallback(() => {
    const current = presets.find((p) => p.id === activeId);
    if (!current) return;
    setPresets((list) => {
      const next = list.filter((p) => p.id !== current.id);
      setActiveId(next[0]?.id ?? null);
      return next;
    });
    trashPreset(current)
      .then(() => {
        // Tell the Settings dialog (if open) to re-fetch its trash list.
        setTrashVersion((v) => v + 1);
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : String(err);
        toast.error("Could not move to trash", msg);
      });
    toast.info("Preset deleted", current.name || "Untitled preset", {
      label: "Undo",
      onClick: () => {
        restoreFromTrash(current.id)
          .then((restored) => {
            handleRestorePreset(restored);
            setTrashVersion((v) => v + 1);
          })
          .catch(() => {
            // Backend may have already restored it (e.g. via Settings);
            // fall back to re-inserting the local copy so undo still works.
            handleRestorePreset(current);
          });
      },
    });
  }, [activeId, handleRestorePreset, presets]);

  const handleReorder = React.useCallback((next: Preset[]) => {
    setPresets(next);
  }, []);

  const handleExport = React.useCallback(() => {
    if (presets.length === 0) {
      toast.info("Nothing to export", "Create a preset first.");
      return;
    }
    exportPresetsToFile(presets)
      .then((path) => {
        if (path) toast.success("Presets exported", path);
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : String(err);
        toast.error("Export failed", msg);
      });
  }, [presets]);

  const handleImport = React.useCallback(() => {
    importPresetsFromFile()
      .then((imported) => {
        if (!imported) return;
        if (imported.length === 0) {
          toast.info("No presets in file");
          return;
        }
        setPresets((list) => [...imported, ...list]);
        setActiveId(imported[0]?.id ?? null);
        toast.success(
          `Imported ${imported.length} preset${imported.length === 1 ? "" : "s"}`,
          "Hotkeys were reset to avoid collisions.",
        );
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : String(err);
        toast.error("Import failed", msg);
      });
  }, []);

  const handlePaste = React.useCallback(
    (id: string) => {
      const target = presets.find((p) => p.id === id);
      if (!target) return;
      pastePreset(id)
        .then(() => {
          toast.success("Pasted", target.name || "Untitled preset");
        })
        .catch((err: unknown) => {
          const message = err instanceof Error ? err.message : String(err);
          toast.error("Paste failed", message);
        });
    },
    [presets],
  );

  const moveSelection = React.useCallback(
    (direction: 1 | -1) => {
      if (presets.length === 0) return;
      const index = presets.findIndex((p) => p.id === activeId);
      const nextIndex =
        index === -1
          ? 0
          : Math.max(0, Math.min(presets.length - 1, index + direction));
      const next = presets[nextIndex];
      if (next) setActiveId(next.id);
    },
    [presets, activeId],
  );

  // Global keyboard shortcuts.
  React.useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      const tag = target?.tagName;
      const isTyping =
        tag === "INPUT" ||
        tag === "TEXTAREA" ||
        (target?.isContentEditable ?? false);

      const mod = e.ctrlKey || e.metaKey;

      // Ctrl+K always works — it's a palette summon, expected even mid-edit.
      if (mod && !e.shiftKey && !e.altKey && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
        return;
      }
      // Ctrl+F focuses search — also expected to work everywhere.
      if (mod && !e.shiftKey && !e.altKey && e.key.toLowerCase() === "f") {
        e.preventDefault();
        searchRef.current?.focus();
        searchRef.current?.select();
        return;
      }
      // Destructive / preset-manipulation shortcuts are suppressed while
      // typing so a caret in the Text field can still receive Ctrl+D /
      // Ctrl+N / Ctrl+Shift+Backspace natively.
      if (isTyping) return;

      if (mod && !e.shiftKey && !e.altKey && e.key.toLowerCase() === "n") {
        e.preventDefault();
        handleCreate();
        return;
      }
      if (mod && !e.shiftKey && !e.altKey && e.key.toLowerCase() === "d") {
        if (!activeId) return;
        e.preventDefault();
        handleDuplicate();
        return;
      }
      if (
        mod &&
        e.shiftKey &&
        !e.altKey &&
        (e.key === "Backspace" || e.key === "Delete")
      ) {
        if (!activeId) return;
        e.preventDefault();
        handleDelete();
        return;
      }
      if (e.key === "ArrowDown" && !mod) {
        e.preventDefault();
        moveSelection(1);
        return;
      }
      if (e.key === "ArrowUp" && !mod) {
        e.preventDefault();
        moveSelection(-1);
        return;
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [activeId, handleCreate, handleDelete, handleDuplicate, moveSelection]);

  return (
    <div className="app-surface flex h-full w-full flex-col">
      <TitleBar
        onOpenSettings={() => setSettingsOpen(true)}
        onOpenPalette={() => setPaletteOpen(true)}
        onImport={handleImport}
        onExport={handleExport}
        activePreset={active}
      />
      <div className="flex min-h-0 flex-1 flex-col gap-2 px-3 pb-3">
        <div className="flex min-h-0 flex-1 gap-0">
          <aside
            className="glass flex shrink-0 flex-col overflow-hidden rounded-lg"
            style={{ width: sidebar.width }}
          >
            <div className="flex items-center gap-2 px-4 pb-2 pt-4">
              <Sparkles className="h-3.5 w-3.5 text-primary" />
              <h2 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                Presets
              </h2>
              <span className="ml-auto font-mono text-[11px] text-muted-foreground">
                {presets.length}
              </span>
            </div>
            <div className="min-h-0 flex-1">
              <PresetList
                presets={presets}
                activeId={activeId}
                query={query}
                conflicts={conflicts}
                searchRef={searchRef}
                onQueryChange={setQuery}
                onSelect={setActiveId}
                onCreate={handleCreate}
                onReorder={handleReorder}
              />
            </div>
          </aside>

          <div
            {...sidebar.handleProps}
            role="separator"
            aria-orientation="vertical"
            aria-label="Resize sidebar"
            className={cn(
              "group relative w-3 shrink-0 cursor-col-resize select-none",
              "touch-none",
            )}
          >
            <span
              aria-hidden="true"
              className={cn(
                "absolute left-1/2 top-1/2 h-10 w-[3px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-border",
                "transition-colors",
                "group-hover:bg-primary/60",
                sidebar.dragging && "bg-primary",
              )}
            />
          </div>

          <main className="glass flex-1 overflow-hidden rounded-lg">
            <div className="relative h-full overflow-y-auto">
              <AnimatePresence mode="wait">
                {active ? (
                  <PresetEditor
                    key={active.id}
                    preset={active}
                    hasConflict={conflicts.has(active.id)}
                    onChange={handleChange}
                    onDuplicate={handleDuplicate}
                    onDelete={handleDelete}
                  />
                ) : (
                  <EmptyState key="empty" onCreate={handleCreate} />
                )}
              </AnimatePresence>
            </div>
          </main>
        </div>

        <StatusBar
          presetCount={presets.length}
          hotkeyCount={hotkeyCount}
          connected={isTauri}
        />
      </div>

      <React.Suspense fallback={null}>
        {settingsOpen ? (
          <SettingsDialog
            open={settingsOpen}
            onClose={() => setSettingsOpen(false)}
            onRestorePreset={handleRestorePreset}
            trashVersion={trashVersion}
          />
        ) : null}
        {paletteOpen ? (
          <CommandPalette
            open={paletteOpen}
            onClose={() => setPaletteOpen(false)}
            presets={presets}
            onSelectPreset={setActiveId}
            onPastePreset={handlePaste}
            onCreatePreset={handleCreate}
            onOpenSettings={() => setSettingsOpen(true)}
          />
        ) : null}
      </React.Suspense>
      <Toaster />
    </div>
  );
}
