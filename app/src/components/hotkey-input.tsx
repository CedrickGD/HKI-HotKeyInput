import * as React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Keyboard, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type Hotkey = string;

function formatKey(e: KeyboardEvent): string | null {
  const parts: string[] = [];
  if (e.ctrlKey) parts.push("Ctrl");
  if (e.shiftKey) parts.push("Shift");
  if (e.altKey) parts.push("Alt");
  if (e.metaKey) parts.push("Win");
  const key = e.key;
  if (["Control", "Shift", "Alt", "Meta"].includes(key)) return null;
  let named = key.length === 1 ? key.toUpperCase() : key;
  if (named === " ") named = "Space";
  parts.push(named);
  return parts.join("+");
}

export function HotkeyInput({
  value,
  onChange,
  placeholder = "Click to record…",
  className,
}: {
  value: Hotkey;
  onChange: (v: Hotkey) => void;
  placeholder?: string;
  className?: string;
}) {
  const [recording, setRecording] = React.useState(false);
  const ref = React.useRef<HTMLButtonElement>(null);
  const reduceMotion = useReducedMotion();

  React.useEffect(() => {
    if (!recording) return;
    function onKey(e: KeyboardEvent) {
      e.preventDefault();
      e.stopPropagation();
      const formatted = formatKey(e);
      if (formatted) {
        onChange(formatted);
        setRecording(false);
        ref.current?.blur();
      }
    }
    window.addEventListener("keydown", onKey, { capture: true });
    return () =>
      window.removeEventListener("keydown", onKey, { capture: true });
  }, [recording, onChange]);

  const tokens = value ? value.split("+") : [];

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <motion.button
        ref={ref}
        type="button"
        onClick={() => setRecording((r) => !r)}
        onBlur={() => setRecording(false)}
        whileTap={{ scale: 0.98 }}
        className={cn(
          "group relative flex min-h-9 flex-1 items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm",
          "border border-input bg-background transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-background",
          recording && "border-primary ring-2 ring-primary/30",
        )}
      >
        <Keyboard
          className={cn(
            "h-4 w-4 shrink-0 transition-colors",
            recording ? "text-primary" : "text-muted-foreground",
          )}
        />
        {tokens.length > 0 ? (
          <span className="flex flex-wrap items-center gap-1">
            {tokens.map((t, i) => (
              <React.Fragment key={i}>
                <kbd
                  className={cn(
                    "inline-flex h-6 min-w-6 items-center justify-center rounded-sm px-1.5 font-mono text-[11px] font-semibold",
                    "border border-border bg-muted/60 text-foreground shadow-[inset_0_-1px_0_hsl(var(--border))]",
                  )}
                >
                  {t}
                </kbd>
                {i < tokens.length - 1 && (
                  <span className="text-muted-foreground/60">+</span>
                )}
              </React.Fragment>
            ))}
          </span>
        ) : (
          <span className="text-muted-foreground">
            {recording ? "Press a key combination…" : placeholder}
          </span>
        )}
        {recording && (
          <motion.span
            layoutId="hki-rec-dot"
            className="ml-auto h-2 w-2 rounded-full bg-primary"
            animate={reduceMotion ? { opacity: 1 } : { opacity: [1, 0.35, 1] }}
            transition={
              reduceMotion
                ? { duration: 0 }
                : { duration: 1.1, repeat: Infinity, ease: "easeInOut" }
            }
          />
        )}
      </motion.button>
      {value && !recording && (
        <button
          type="button"
          onClick={() => onChange("")}
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-md",
            "text-muted-foreground hover:bg-accent hover:text-foreground transition-colors",
          )}
          aria-label="Clear hotkey"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
