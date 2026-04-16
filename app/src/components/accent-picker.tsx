import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Palette } from "lucide-react";
import { useTheme } from "@/theme/use-theme";
import { cn } from "@/lib/utils";

const SWATCHES: { name: string; hex: string }[] = [
  { name: "Violet", hex: "#8b5cf6" },
  { name: "Indigo", hex: "#6366f1" },
  { name: "Sky", hex: "#0ea5e9" },
  { name: "Cyan", hex: "#06b6d4" },
  { name: "Emerald", hex: "#10b981" },
  { name: "Lime", hex: "#84cc16" },
  { name: "Amber", hex: "#f59e0b" },
  { name: "Rose", hex: "#f43f5e" },
  { name: "Pink", hex: "#ec4899" },
  { name: "Fuchsia", hex: "#d946ef" },
];

export function AccentPicker({ className }: { className?: string }) {
  const { accent, setAccent } = useTheme();
  const [open, setOpen] = React.useState(false);
  const [customHex, setCustomHex] = React.useState(accent);
  const popoverRef = React.useRef<HTMLDivElement>(null);
  const buttonRef = React.useRef<HTMLButtonElement>(null);

  React.useEffect(() => setCustomHex(accent), [accent]);

  React.useEffect(() => {
    if (!open) return;
    function onClick(e: MouseEvent) {
      const t = e.target as Node;
      if (
        popoverRef.current &&
        !popoverRef.current.contains(t) &&
        buttonRef.current &&
        !buttonRef.current.contains(t)
      ) {
        setOpen(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("mousedown", onClick);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("mousedown", onClick);
      window.removeEventListener("keydown", onKey);
    };
  }, [open]);

  function commitCustom(value: string) {
    const v = value.startsWith("#") ? value : `#${value}`;
    if (/^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(v)) {
      setAccent(v);
    }
  }

  return (
    <div className={cn("relative", className)}>
      <motion.button
        ref={buttonRef}
        type="button"
        onClick={() => setOpen((o) => !o)}
        whileTap={{ scale: 0.92 }}
        whileHover={{ scale: 1.05 }}
        transition={{ type: "spring", stiffness: 400, damping: 22 }}
        aria-label="Pick accent color"
        className={cn(
          "relative flex h-9 w-9 items-center justify-center rounded-full",
          "border border-border bg-card/70 backdrop-blur-sm shadow-soft overflow-hidden",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        )}
      >
        <span
          className="absolute inset-[3px] rounded-full"
          style={{
            background: `conic-gradient(from 140deg, ${accent}, hsl(var(--primary)/0.4), ${accent})`,
          }}
        />
        <span className="relative flex h-[18px] w-[18px] items-center justify-center rounded-full bg-background/70">
          <Palette className="h-[13px] w-[13px] text-foreground/80" strokeWidth={2.25} />
        </span>
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            ref={popoverRef}
            initial={{ opacity: 0, y: -6, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.96 }}
            transition={{ type: "spring", stiffness: 340, damping: 26 }}
            className={cn(
              "absolute right-0 top-11 z-50 w-64 rounded-lg p-3",
              "glass shadow-glow",
            )}
          >
            <div className="mb-2 flex items-center justify-between px-1">
              <span className="text-xs font-medium text-muted-foreground">
                Accent
              </span>
              <span className="font-mono text-[10px] text-muted-foreground">
                {accent.toUpperCase()}
              </span>
            </div>
            <div className="grid grid-cols-5 gap-2">
              {SWATCHES.map((s) => {
                const active = s.hex.toLowerCase() === accent.toLowerCase();
                return (
                  <motion.button
                    key={s.hex}
                    type="button"
                    onClick={() => setAccent(s.hex)}
                    whileTap={{ scale: 0.88 }}
                    whileHover={{ scale: 1.1, y: -1 }}
                    title={s.name}
                    className={cn(
                      "relative flex h-9 w-9 items-center justify-center rounded-md",
                      "transition-shadow",
                      active
                        ? "ring-2 ring-offset-2 ring-offset-card"
                        : "ring-0",
                    )}
                    style={{
                      backgroundColor: s.hex,
                      ...(active
                        ? ({ ["--tw-ring-color" as string]: s.hex } as React.CSSProperties)
                        : {}),
                    }}
                  >
                    {active && (
                      <Check className="h-4 w-4 text-white drop-shadow" strokeWidth={3} />
                    )}
                  </motion.button>
                );
              })}
            </div>
            <div className="mt-3 flex items-center gap-2 rounded-md border border-border/80 bg-background/60 p-1.5">
              <label
                className="relative h-6 w-6 shrink-0 cursor-pointer overflow-hidden rounded-md border border-border"
                style={{ backgroundColor: customHex }}
                title="Custom color"
              >
                <input
                  type="color"
                  value={/^#([0-9a-f]{6})$/i.test(customHex) ? customHex : accent}
                  onChange={(e) => {
                    setCustomHex(e.target.value);
                    commitCustom(e.target.value);
                  }}
                  className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
                />
              </label>
              <input
                type="text"
                value={customHex}
                onChange={(e) => setCustomHex(e.target.value)}
                onBlur={(e) => commitCustom(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") commitCustom(e.currentTarget.value);
                }}
                placeholder="#RRGGBB"
                spellCheck={false}
                className={cn(
                  "h-7 w-full rounded-sm bg-transparent px-1 font-mono text-xs",
                  "text-foreground placeholder:text-muted-foreground/70",
                  "outline-none focus:ring-0",
                )}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
