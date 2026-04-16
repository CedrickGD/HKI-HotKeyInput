import * as React from "react";

export type ThemeMode = "dark" | "light";

export type ThemeCtx = {
  mode: ThemeMode;
  accent: string;
  setMode: (m: ThemeMode) => void;
  toggleMode: () => void;
  setAccent: (hex: string) => void;
};

export const ThemeContext = React.createContext<ThemeCtx | null>(null);
