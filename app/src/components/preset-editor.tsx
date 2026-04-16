import * as React from "react";
import { motion, AnimatePresence, LayoutGroup } from "framer-motion";
import {
  AlertTriangle,
  Braces,
  Copy,
  Edit3,
  Eye,
  Plus,
  Trash2,
  Variable,
} from "lucide-react";
import type { Placeholder, Preset } from "@/types";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tooltip } from "@/components/ui/tooltip";
import { HotkeyInput } from "@/components/hotkey-input";
import { cn } from "@/lib/utils";

type PresetEditorProps = {
  preset: Preset;
  hasConflict: boolean;
  onChange: (p: Preset) => void;
  onDuplicate: () => void;
  onDelete: () => void;
};

type TabKey = "edit" | "preview";

export function PresetEditor({
  preset,
  hasConflict,
  onChange,
  onDuplicate,
  onDelete,
}: PresetEditorProps) {
  const [tab, setTab] = React.useState<TabKey>("edit");

  function update<K extends keyof Preset>(k: K, v: Preset[K]) {
    onChange({ ...preset, [k]: v });
  }

  function addPlaceholder() {
    const ph: Placeholder = {
      id: crypto.randomUUID(),
      key: `var${preset.placeholders.length + 1}`,
      label: "",
    };
    update("placeholders", [...preset.placeholders, ph]);
  }

  function updatePlaceholder(id: string, patch: Partial<Placeholder>) {
    update(
      "placeholders",
      preset.placeholders.map((p) => (p.id === id ? { ...p, ...patch } : p)),
    );
  }

  function removePlaceholder(id: string) {
    update(
      "placeholders",
      preset.placeholders.filter((p) => p.id !== id),
    );
  }

  return (
    <motion.div
      key={preset.id}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
      className="mx-auto flex h-full w-full max-w-3xl flex-col gap-4 p-6"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <Input
            value={preset.name}
            onChange={(e) => update("name", e.target.value)}
            placeholder="Preset name"
            aria-label="Preset name"
            className={cn(
              "h-auto border-0 bg-transparent px-0 text-2xl font-semibold tracking-tight",
              "shadow-none focus-visible:ring-0 focus-visible:ring-offset-0",
              "placeholder:text-muted-foreground/60",
            )}
          />
          <p className="mt-1 text-sm text-muted-foreground">
            Assign a hotkey and write the text to paste.
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <Tooltip content="Duplicate (Ctrl+D)" side="bottom">
            <Button
              variant="ghost"
              size="icon"
              onClick={onDuplicate}
              aria-label="Duplicate preset"
            >
              <Copy className="h-4 w-4" />
            </Button>
          </Tooltip>
          <Tooltip content="Delete (Ctrl+Shift+Backspace)" side="bottom">
            <Button
              variant="ghost"
              size="icon"
              onClick={onDelete}
              aria-label="Delete preset"
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </Tooltip>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Variable className="h-4 w-4 text-primary" />
            Hotkey
          </CardTitle>
          <CardDescription>
            A global shortcut that pastes this preset into the focused field.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <HotkeyInput
            value={preset.hotkey}
            onChange={(v) => update("hotkey", v)}
          />
          {hasConflict ? (
            <div className="flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-600 dark:text-amber-400">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>
                Another preset is already using this hotkey. Only one will fire
                when pressed.
              </span>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card className="flex flex-1 flex-col">
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Braces className="h-4 w-4 text-primary" />
              Text
            </CardTitle>
            <CardDescription>
              Use{" "}
              <code className="font-mono text-[11px] text-foreground">
                {"{var}"}
              </code>{" "}
              tokens for placeholders.
            </CardDescription>
          </div>
          <TabSwitcher value={tab} onChange={setTab} />
        </CardHeader>
        <CardContent className="flex-1">
          <AnimatePresence mode="wait" initial={false}>
            {tab === "edit" ? (
              <motion.div
                key="edit"
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.14 }}
                className="h-full"
              >
                <Textarea
                  value={preset.text}
                  onChange={(e) => update("text", e.target.value)}
                  placeholder="Hello {name}, thanks for reaching out!"
                  aria-label="Preset text"
                  className="h-full min-h-[180px] font-mono text-sm"
                />
              </motion.div>
            ) : (
              <motion.div
                key="preview"
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.14 }}
                className="h-full"
              >
                <PreviewPanel preset={preset} />
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm">Placeholders</CardTitle>
            <CardDescription>
              Prompted values filled at paste time.
            </CardDescription>
          </div>
          <Button size="sm" variant="outline" onClick={addPlaceholder}>
            <Plus className="h-3.5 w-3.5" /> Add
          </Button>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <AnimatePresence initial={false}>
            {preset.placeholders.map((p) => (
              <motion.div
                key={p.id}
                layout
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -8 }}
                transition={{ type: "spring", stiffness: 360, damping: 30 }}
                className="flex items-center gap-2"
              >
                <div className="relative flex-1">
                  <span className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 font-mono text-xs text-muted-foreground">
                    {"{"}
                  </span>
                  <Input
                    value={p.key}
                    onChange={(e) =>
                      updatePlaceholder(p.id, { key: e.target.value })
                    }
                    placeholder="name"
                    aria-label="Placeholder key"
                    className="pl-6 pr-5 font-mono text-sm"
                  />
                  <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 font-mono text-xs text-muted-foreground">
                    {"}"}
                  </span>
                </div>
                <Input
                  value={p.label}
                  onChange={(e) =>
                    updatePlaceholder(p.id, { label: e.target.value })
                  }
                  placeholder="Label shown at paste time"
                  aria-label="Placeholder label"
                  className="flex-[2]"
                />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removePlaceholder(p.id)}
                  aria-label="Remove placeholder"
                >
                  <Trash2 className="h-4 w-4 text-muted-foreground" />
                </Button>
              </motion.div>
            ))}
          </AnimatePresence>
          {preset.placeholders.length === 0 && (
            <p className="py-2 text-center text-xs text-muted-foreground">
              No placeholders yet.
            </p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

function TabSwitcher({
  value,
  onChange,
}: {
  value: TabKey;
  onChange: (t: TabKey) => void;
}) {
  const tabs: { key: TabKey; label: string; icon: React.ReactNode }[] = [
    { key: "edit", label: "Edit", icon: <Edit3 className="h-3 w-3" /> },
    { key: "preview", label: "Preview", icon: <Eye className="h-3 w-3" /> },
  ];
  return (
    <LayoutGroup>
      <div
        role="tablist"
        aria-label="Editor mode"
        className="relative inline-flex items-center gap-0.5 rounded-md border border-border bg-muted/40 p-0.5"
      >
        {tabs.map((t) => {
          const active = t.key === value;
          return (
            <button
              key={t.key}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => onChange(t.key)}
              className={cn(
                "relative z-10 inline-flex h-7 items-center gap-1 rounded-sm px-2 text-[11px] font-medium transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                active ? "text-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {active && (
                <motion.span
                  layoutId="tab-indicator"
                  className="absolute inset-0 -z-10 rounded-sm bg-card shadow-soft"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
              {t.icon}
              {t.label}
            </button>
          );
        })}
      </div>
    </LayoutGroup>
  );
}

function PreviewPanel({ preset }: { preset: Preset }) {
  const [values, setValues] = React.useState<Record<string, string>>(() =>
    Object.fromEntries(preset.placeholders.map((p) => [p.key, ""])),
  );

  React.useEffect(() => {
    setValues((prev) => {
      const next: Record<string, string> = {};
      for (const p of preset.placeholders) next[p.key] = prev[p.key] ?? "";
      return next;
    });
  }, [preset.placeholders]);

  const resolved = React.useMemo(() => {
    return preset.text.replace(/\{([a-zA-Z0-9_]+)\}/g, (_, k: string) => {
      const v = values[k];
      return v && v.length > 0 ? v : `{${k}}`;
    });
  }, [preset.text, values]);

  return (
    <div className="flex h-full min-h-[180px] flex-col gap-3">
      {preset.placeholders.length > 0 ? (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {preset.placeholders.map((p) => (
            <label key={p.id} className="flex flex-col gap-1">
              <span className="flex items-center gap-1 text-[11px] font-medium text-muted-foreground">
                <code className="font-mono">{`{${p.key}}`}</code>
                {p.label ? (
                  <span className="truncate text-muted-foreground/70">
                    {p.label}
                  </span>
                ) : null}
              </span>
              <Input
                value={values[p.key] ?? ""}
                onChange={(e) =>
                  setValues((v) => ({ ...v, [p.key]: e.target.value }))
                }
                placeholder={p.label || p.key}
                className="h-8 text-xs"
              />
            </label>
          ))}
        </div>
      ) : null}
      <div className="flex-1 overflow-auto rounded-md border border-border/60 bg-muted/30 p-3 font-mono text-sm whitespace-pre-wrap">
        {resolved.length > 0 ? (
          resolved
        ) : (
          <span className="text-muted-foreground">
            Start typing text to see the preview.
          </span>
        )}
      </div>
    </div>
  );
}
