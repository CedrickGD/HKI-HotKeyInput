export type HSL = { h: number; s: number; l: number };

export function hexToHsl(hex: string): HSL {
  const clean = hex.replace("#", "").trim();
  const full =
    clean.length === 3
      ? clean.split("").map((c) => c + c).join("")
      : clean;
  const r = parseInt(full.slice(0, 2), 16) / 255;
  const g = parseInt(full.slice(2, 4), 16) / 255;
  const b = parseInt(full.slice(4, 6), 16) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const l = (max + min) / 2;
  let h = 0;
  let s = 0;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0);
        break;
      case g:
        h = (b - r) / d + 2;
        break;
      case b:
        h = (r - g) / d + 4;
        break;
    }
    h *= 60;
  }
  return { h: Math.round(h), s: Math.round(s * 100), l: Math.round(l * 100) };
}

export function hslToCssTriplet({ h, s, l }: HSL): string {
  return `${h} ${s}% ${l}%`;
}

export function hexToHslTriplet(hex: string): string {
  return hslToCssTriplet(hexToHsl(hex));
}

export function readableForeground(hex: string): string {
  const { l } = hexToHsl(hex);
  return l > 60 ? "240 10% 8%" : "0 0% 100%";
}
