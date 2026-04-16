import * as React from "react";
import { motion, AnimatePresence, Reorder, useDragControls } from "framer-motion";
import { AlertTriangle, FileText, GripVertical, Plus, Search } from "lucide-react";
import type { Preset } from "@/types";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tooltip } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

type PresetListProps = {
  presets: Preset[];
  activeId: string | null;
  query: string;
  conflicts: Set<string>;
  searchRef: React.RefObject<HTMLInputElement | null>;
  onQueryChange: (s: string) => void;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onReorder: (next: Preset[]) => void;
};

export function PresetList({
  presets,
  activeId,
  query,
  conflicts,
  searchRef,
  onQueryChange,
  onSelect,
  onCreate,
  onReorder,
}: PresetListProps) {
  const normalized = query.trim().toLowerCase();
  const isFiltering = normalized.length > 0;
  const filtered = isFiltering
    ? presets.filter(
        (p) =>
          p.name.toLowerCase().includes(normalized) ||
          p.hotkey.toLowerCase().includes(normalized),
      )
    : presets;

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-4 pb-3">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            ref={searchRef}
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="Search presets…"
            aria-label="Search presets"
            className="h-9 pl-8"
          />
        </div>
        <Tooltip content="New preset (Ctrl+N)" side="bottom">
          <Button size="icon" onClick={onCreate} aria-label="New preset">
            <Plus className="h-4 w-4" />
          </Button>
        </Tooltip>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-3">
        {isFiltering ? (
          <AnimatePresence initial={false}>
            {filtered.map((p) => (
              <PresetRow
                key={p.id}
                preset={p}
                active={p.id === activeId}
                hasConflict={conflicts.has(p.id)}
                draggable={false}
                onSelect={() => onSelect(p.id)}
              />
            ))}
          </AnimatePresence>
        ) : (
          <Reorder.Group
            axis="y"
            values={presets}
            onReorder={onReorder}
            className="flex flex-col"
          >
            {presets.map((p) => (
              <DraggableRow
                key={p.id}
                preset={p}
                active={p.id === activeId}
                hasConflict={conflicts.has(p.id)}
                onSelect={() => onSelect(p.id)}
              />
            ))}
          </Reorder.Group>
        )}

        {filtered.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center gap-2 px-4 py-10 text-center text-sm text-muted-foreground"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
              <Search className="h-4 w-4" />
            </div>
            <span>
              {isFiltering
                ? `No presets match “${query}”.`
                : "No presets yet. Create one to get started."}
            </span>
          </motion.div>
        )}
      </div>
    </div>
  );
}

function DraggableRow({
  preset,
  active,
  hasConflict,
  onSelect,
}: {
  preset: Preset;
  active: boolean;
  hasConflict: boolean;
  onSelect: () => void;
}) {
  const controls = useDragControls();
  return (
    <Reorder.Item
      value={preset}
      dragListener={false}
      dragControls={controls}
      layout
      className="list-none"
    >
      <RowInner
        preset={preset}
        active={active}
        hasConflict={hasConflict}
        onSelect={onSelect}
        onDragPointerDown={(e) => controls.start(e)}
      />
    </Reorder.Item>
  );
}

function PresetRow({
  preset,
  active,
  hasConflict,
  onSelect,
}: {
  preset: Preset;
  active: boolean;
  hasConflict: boolean;
  draggable: boolean;
  onSelect: () => void;
}) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{ type: "spring", stiffness: 340, damping: 28 }}
    >
      <RowInner
        preset={preset}
        active={active}
        hasConflict={hasConflict}
        onSelect={onSelect}
      />
    </motion.div>
  );
}

function RowInner({
  preset,
  active,
  hasConflict,
  onSelect,
  onDragPointerDown,
}: {
  preset: Preset;
  active: boolean;
  hasConflict: boolean;
  onSelect: () => void;
  onDragPointerDown?: (e: React.PointerEvent) => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "group relative w-full rounded-md px-3 py-2.5 text-left transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-background",
        "hover:bg-accent/70",
        active && "bg-accent",
      )}
    >
      {active && (
        <motion.span
          layoutId="preset-active-bar"
          className="absolute inset-y-1.5 left-0 w-[3px] rounded-full bg-primary"
          transition={{ type: "spring", stiffness: 360, damping: 28 }}
        />
      )}
      {onDragPointerDown ? (
        <span
          onPointerDown={(e) => {
            e.stopPropagation();
            onDragPointerDown(e);
          }}
          onClick={(e) => e.stopPropagation()}
          className={cn(
            "absolute right-1.5 top-1/2 flex h-6 w-4 -translate-y-1/2 cursor-grab items-center justify-center rounded-sm text-muted-foreground/60",
            "transition-opacity active:cursor-grabbing",
            "opacity-0 group-hover:opacity-100",
          )}
          aria-hidden="true"
        >
          <GripVertical className="h-3.5 w-3.5" />
        </span>
      ) : null}
      <div className="flex items-center gap-3">
        <div
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-md",
            active
              ? "bg-primary/15 text-primary"
              : "bg-muted text-muted-foreground",
          )}
        >
          <FileText className="h-[15px] w-[15px]" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <span className="truncate text-sm font-medium text-foreground">
              {preset.name || "Untitled preset"}
            </span>
            {hasConflict ? (
              <Tooltip content="Hotkey conflict" side="right">
                <span className="inline-flex text-amber-500">
                  <AlertTriangle className="h-3.5 w-3.5" />
                </span>
              </Tooltip>
            ) : null}
          </div>
          <div className="mt-1 flex items-center gap-1.5">
            {preset.hotkey ? (
              <Badge variant="default" className="truncate">
                {preset.hotkey}
              </Badge>
            ) : (
              <Badge variant="muted">No hotkey</Badge>
            )}
            {preset.placeholders.length > 0 && (
              <Badge variant="outline">
                {preset.placeholders.length} var
                {preset.placeholders.length === 1 ? "" : "s"}
              </Badge>
            )}
          </div>
        </div>
      </div>
    </button>
  );
}
