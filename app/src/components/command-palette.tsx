import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ClipboardPaste,
  CornerDownLeft,
  FileText,
  Moon,
  Plus,
  Search,
  Settings as SettingsIcon,
  Sun,
} from "lucide-react";
import type { Preset } from "@/types";
import { cn } from "@/lib/utils";
import { useTheme } from "@/theme/use-theme";

export type CommandItem = {
  id: string;
  label: string;
  hint?: string;
  icon: React.ReactNode;
  section: "presets" | "theme" | "actions";
  run: () => void;
};

type CommandPaletteProps = {
  open: boolean;
  onClose: () => void;
  presets: Preset[];
  onSelectPreset: (id: string) => void;
  onPastePreset: (id: string) => void;
  onCreatePreset: () => void;
  onOpenSettings: () => void;
};

export function CommandPalette({
  open,
  onClose,
  presets,
  onSelectPreset,
  onPastePreset,
  onCreatePreset,
  onOpenSettings,
}: CommandPaletteProps) {
  const { mode, toggleMode } = useTheme();
  const [query, setQuery] = React.useState("");
  const [activeIndex, setActiveIndex] = React.useState(0);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const listRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (open) {
      setQuery("");
      setActiveIndex(0);
      // Focus next tick so AnimatePresence has mounted the element.
      const id = window.setTimeout(() => inputRef.current?.focus(), 10);
      return () => window.clearTimeout(id);
    }
    return undefined;
  }, [open]);

  const items = React.useMemo<CommandItem[]>(() => {
    const presetItems: CommandItem[] = [];
    for (const p of presets) {
      presetItems.push({
        id: `preset:${p.id}`,
        label: p.name || "Untitled preset",
        hint: p.hotkey || "No hotkey",
        icon: <FileText className="h-4 w-4" />,
        section: "presets",
        run: () => {
          onSelectPreset(p.id);
          onClose();
        },
      });
      presetItems.push({
        id: `paste:${p.id}`,
        label: `Paste: ${p.name || "Untitled preset"}`,
        hint: p.hotkey || undefined,
        icon: <ClipboardPaste className="h-4 w-4" />,
        section: "presets",
        run: () => {
          onPastePreset(p.id);
          onClose();
        },
      });
    }
    const actionItems: CommandItem[] = [
      {
        id: "action:new",
        label: "Create new preset",
        hint: "Ctrl+N",
        icon: <Plus className="h-4 w-4" />,
        section: "actions",
        run: () => {
          onCreatePreset();
          onClose();
        },
      },
      {
        id: "action:settings",
        label: "Open settings",
        icon: <SettingsIcon className="h-4 w-4" />,
        section: "actions",
        run: () => {
          onOpenSettings();
          onClose();
        },
      },
    ];
    const themeItems: CommandItem[] = [
      {
        id: "theme:toggle",
        label: mode === "dark" ? "Switch to light mode" : "Switch to dark mode",
        icon:
          mode === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          ),
        section: "theme",
        run: () => {
          toggleMode();
          onClose();
        },
      },
    ];
    return [...actionItems, ...presetItems, ...themeItems];
  }, [
    presets,
    mode,
    onSelectPreset,
    onPastePreset,
    onCreatePreset,
    onOpenSettings,
    onClose,
    toggleMode,
  ]);

  const filtered = React.useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter(
      (i) =>
        i.label.toLowerCase().includes(q) ||
        (i.hint ? i.hint.toLowerCase().includes(q) : false),
    );
  }, [items, query]);

  React.useEffect(() => {
    if (activeIndex >= filtered.length) setActiveIndex(0);
  }, [activeIndex, filtered.length]);

  const grouped = React.useMemo(() => {
    const sections: { key: CommandItem["section"]; title: string; items: CommandItem[] }[] = [
      { key: "actions", title: "Actions", items: [] },
      { key: "presets", title: "Presets", items: [] },
      { key: "theme", title: "Theme", items: [] },
    ];
    for (const item of filtered) {
      const s = sections.find((x) => x.key === item.section);
      if (s) s.items.push(item);
    }
    return sections.filter((s) => s.items.length > 0);
  }, [filtered]);

  function onKey(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(filtered.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(0, i - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      filtered[activeIndex]?.run();
    } else if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    }
  }

  React.useEffect(() => {
    if (!listRef.current) return;
    const el = listRef.current.querySelector<HTMLElement>(
      `[data-cmd-index="${activeIndex}"]`,
    );
    el?.scrollIntoView({ block: "nearest" });
  }, [activeIndex]);

  return (
    <AnimatePresence>
      {open && (
        <div
          role="dialog"
          aria-label="Command palette"
          aria-modal="true"
          className="fixed inset-0 z-[55] flex items-start justify-center p-4 pt-[14vh]"
        >
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={onClose}
            className="absolute inset-0 bg-background/70 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, y: -12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 340, damping: 28 }}
            className={cn(
              "relative z-10 w-full max-w-lg overflow-hidden rounded-xl border border-border bg-popover shadow-glow",
            )}
          >
            <div className="flex items-center gap-2 border-b border-border/60 px-3.5 py-3">
              <Search className="h-4 w-4 text-muted-foreground" />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setActiveIndex(0);
                }}
                onKeyDown={onKey}
                placeholder="Type a command or search…"
                className="h-7 flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
              />
              <kbd className="rounded border border-border bg-muted/60 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                Esc
              </kbd>
            </div>

            <div
              ref={listRef}
              className="max-h-[50vh] overflow-y-auto px-1.5 py-1.5"
            >
              {filtered.length === 0 ? (
                <div className="px-3 py-8 text-center text-sm text-muted-foreground">
                  No results for &ldquo;{query}&rdquo;
                </div>
              ) : (
                grouped.map((section) => (
                  <div key={section.key} className="py-1">
                    <div className="px-2.5 pt-1 pb-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                      {section.title}
                    </div>
                    {section.items.map((item) => {
                      const idx = filtered.indexOf(item);
                      const active = idx === activeIndex;
                      return (
                        <button
                          key={item.id}
                          type="button"
                          data-cmd-index={idx}
                          onMouseEnter={() => setActiveIndex(idx)}
                          onClick={() => item.run()}
                          className={cn(
                            "group flex w-full items-center gap-3 rounded-md px-2.5 py-2 text-left text-sm transition-colors",
                            active
                              ? "bg-accent text-accent-foreground"
                              : "hover:bg-accent/60",
                          )}
                        >
                          <span
                            className={cn(
                              "flex h-7 w-7 items-center justify-center rounded-md",
                              active
                                ? "bg-primary/15 text-primary"
                                : "bg-muted text-muted-foreground",
                            )}
                          >
                            {item.icon}
                          </span>
                          <span className="min-w-0 flex-1 truncate">{item.label}</span>
                          {item.hint ? (
                            <span className="font-mono text-[11px] text-muted-foreground">
                              {item.hint}
                            </span>
                          ) : null}
                          {active ? (
                            <CornerDownLeft className="h-3.5 w-3.5 text-muted-foreground" />
                          ) : null}
                        </button>
                      );
                    })}
                  </div>
                ))
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
