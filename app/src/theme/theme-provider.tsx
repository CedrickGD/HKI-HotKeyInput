import * as React from "react";
import { hexToHslTriplet, readableForeground } from "@/lib/color";
import { ThemeContext, type ThemeMode } from "@/theme/theme-context";

const STORAGE_MODE = "hki.theme.mode";
const STORAGE_ACCENT = "hki.theme.accent";
const DEFAULT_ACCENT = "#8b5cf6";

function applyAccent(hex: string) {
  const triplet = hexToHslTriplet(hex);
  const fg = readableForeground(hex);
  document.documentElement.style.setProperty("--primary", triplet);
  document.documentElement.style.setProperty("--ring", triplet);
  document.documentElement.style.setProperty("--primary-foreground", fg);
}

function applyMode(mode: ThemeMode) {
  const root = document.documentElement;
  if (mode === "dark") root.classList.add("dark");
  else root.classList.remove("dark");
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = React.useState<ThemeMode>(() => {
    const stored = localStorage.getItem(STORAGE_MODE) as ThemeMode | null;
    if (stored === "dark" || stored === "light") return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  });
  const [accent, setAccentState] = React.useState<string>(
    () => localStorage.getItem(STORAGE_ACCENT) || DEFAULT_ACCENT,
  );

  React.useEffect(() => {
    applyMode(mode);
    localStorage.setItem(STORAGE_MODE, mode);
  }, [mode]);

  React.useEffect(() => {
    applyAccent(accent);
    localStorage.setItem(STORAGE_ACCENT, accent);
  }, [accent]);

  const value = React.useMemo(
    () => ({
      mode,
      accent,
      setMode: setModeState,
      toggleMode: () => setModeState((m) => (m === "dark" ? "light" : "dark")),
      setAccent: setAccentState,
    }),
    [mode, accent],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
