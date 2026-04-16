import { Command, Keyboard, List } from "lucide-react";
import { cn } from "@/lib/utils";

export function StatusBar({
  presetCount,
  hotkeyCount,
  connected,
}: {
  presetCount: number;
  hotkeyCount: number;
  connected: boolean;
}) {
  return (
    <footer className="glass flex h-7 shrink-0 items-center justify-between gap-3 rounded-md px-3 text-[11px] text-muted-foreground">
      <div className="flex items-center gap-4">
        <span className="inline-flex items-center gap-1.5">
          <span
            aria-hidden="true"
            className={cn(
              "inline-block h-1.5 w-1.5 rounded-full",
              connected ? "bg-emerald-500" : "bg-amber-500",
            )}
          />
          <span>{connected ? "Backend connected" : "Preview (no backend)"}</span>
        </span>
        <span className="inline-flex items-center gap-1.5">
          <List className="h-3 w-3" />
          <span className="font-mono">{presetCount}</span> preset
          {presetCount === 1 ? "" : "s"}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Keyboard className="h-3 w-3" />
          <span className="font-mono">{hotkeyCount}</span> hotkey
          {hotkeyCount === 1 ? "" : "s"} registered
        </span>
      </div>
      <div className="flex items-center gap-1.5">
        <Command className="h-3 w-3" />
        <span>
          <kbd className="rounded-sm border border-border bg-muted/50 px-1 font-mono text-[10px]">
            Ctrl
          </kbd>
          <span className="mx-0.5">+</span>
          <kbd className="rounded-sm border border-border bg-muted/50 px-1 font-mono text-[10px]">
            K
          </kbd>
          <span className="ml-1.5">for command palette</span>
        </span>
      </div>
    </footer>
  );
}
