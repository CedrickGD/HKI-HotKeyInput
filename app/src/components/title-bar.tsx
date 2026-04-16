import { Command, Download, FileText, Settings, Upload } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { AccentPicker } from "@/components/accent-picker";
import { Tooltip } from "@/components/ui/tooltip";
import { dragRegion, noDragRegion } from "@/lib/drag-region";
import { cn } from "@/lib/utils";
import type { Preset } from "@/types";

type TitleBarProps = {
  onOpenSettings: () => void;
  onOpenPalette: () => void;
  onImport: () => void;
  onExport: () => void;
  activePreset: Preset | null;
};

export function TitleBar({
  onOpenSettings,
  onOpenPalette,
  onImport,
  onExport,
  activePreset,
}: TitleBarProps) {
  return (
    <header
      className="relative flex h-12 shrink-0 items-center justify-between px-4 select-none"
      style={dragRegion}
    >
      {/* Left cluster — Import / Export */}
      <div className="flex items-center gap-1.5" style={noDragRegion}>
        <Tooltip content="Import presets" side="bottom">
          <button
            type="button"
            onClick={onImport}
            aria-label="Import presets"
            className={cn(
              "flex h-9 items-center gap-1.5 rounded-md border border-border bg-card/70 px-2.5 text-[11px] font-medium text-muted-foreground backdrop-blur-sm",
              "transition-colors hover:bg-accent hover:text-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            )}
          >
            <Upload className="h-3.5 w-3.5" />
            <span>Import</span>
          </button>
        </Tooltip>
        <Tooltip content="Export presets" side="bottom">
          <button
            type="button"
            onClick={onExport}
            aria-label="Export presets"
            className={cn(
              "flex h-9 items-center gap-1.5 rounded-md border border-border bg-card/70 px-2.5 text-[11px] font-medium text-muted-foreground backdrop-blur-sm",
              "transition-colors hover:bg-accent hover:text-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            )}
          >
            <Download className="h-3.5 w-3.5" />
            <span>Export</span>
          </button>
        </Tooltip>
      </div>

      {/* Centered live context — currently selected preset + hotkey */}
      {activePreset ? (
        <div className="pointer-events-none absolute left-1/2 top-1/2 flex max-w-[38%] -translate-x-1/2 -translate-y-1/2 items-center gap-2 text-muted-foreground">
          <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground/70" />
          <span className="truncate text-[12px] font-medium text-foreground/90">
            {activePreset.name || "Untitled preset"}
          </span>
          {activePreset.hotkey ? (
            <kbd className="shrink-0 rounded-sm border border-border bg-muted/60 px-1.5 py-0.5 font-mono text-[10px] text-foreground/80">
              {activePreset.hotkey}
            </kbd>
          ) : null}
        </div>
      ) : null}

      {/* Right cluster — palette, settings, accent, theme */}
      <div className="flex items-center gap-1.5" style={noDragRegion}>
        <Tooltip content="Command palette (Ctrl+K)" side="bottom">
          <button
            type="button"
            onClick={onOpenPalette}
            aria-label="Open command palette"
            className={cn(
              "flex h-9 items-center gap-1.5 rounded-md border border-border bg-card/70 px-2.5 text-[11px] text-muted-foreground backdrop-blur-sm",
              "transition-colors hover:bg-accent hover:text-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            )}
          >
            <Command className="h-3.5 w-3.5" />
            <span>
              <kbd className="font-mono text-[10px]">Ctrl</kbd>
              <span className="mx-0.5">+</span>
              <kbd className="font-mono text-[10px]">K</kbd>
            </span>
          </button>
        </Tooltip>
        <Tooltip content="Settings" side="bottom">
          <button
            type="button"
            onClick={onOpenSettings}
            aria-label="Open settings"
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-full border border-border bg-card/70 backdrop-blur-sm shadow-soft",
              "text-foreground/80 transition-colors hover:bg-accent hover:text-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            )}
          >
            <Settings className="h-[18px] w-[18px]" />
          </button>
        </Tooltip>
        <AccentPicker />
        <ThemeToggle />
      </div>
    </header>
  );
}
