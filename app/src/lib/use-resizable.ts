import * as React from "react";

export type UseResizableOptions = {
  storageKey?: string;
  defaultWidth: number;
  min: number;
  max: number;
};

/**
 * Lightweight horizontal resizer hook. Returns a width, a setter, and the
 * handle props to spread onto the drag element. Persists to localStorage
 * when a key is provided.
 */
export function useResizable({
  storageKey,
  defaultWidth,
  min,
  max,
}: UseResizableOptions) {
  const [width, setWidth] = React.useState<number>(() => {
    if (!storageKey) return defaultWidth;
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) return defaultWidth;
      const parsed = Number.parseInt(raw, 10);
      if (Number.isFinite(parsed)) {
        return Math.min(max, Math.max(min, parsed));
      }
    } catch {
      /* ignore */
    }
    return defaultWidth;
  });
  const [dragging, setDragging] = React.useState(false);
  const originX = React.useRef(0);
  const originWidth = React.useRef(defaultWidth);

  React.useEffect(() => {
    if (!storageKey) return;
    try {
      localStorage.setItem(storageKey, String(width));
    } catch {
      /* ignore */
    }
  }, [storageKey, width]);

  const onPointerDown = React.useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.currentTarget.setPointerCapture(e.pointerId);
      originX.current = e.clientX;
      originWidth.current = width;
      setDragging(true);
    },
    [width],
  );

  const onPointerMove = React.useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (!dragging) return;
      const delta = e.clientX - originX.current;
      const next = Math.min(max, Math.max(min, originWidth.current + delta));
      setWidth(next);
    },
    [dragging, min, max],
  );

  const stop = React.useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (e.currentTarget.hasPointerCapture(e.pointerId)) {
      e.currentTarget.releasePointerCapture(e.pointerId);
    }
    setDragging(false);
  }, []);

  return {
    width,
    setWidth,
    dragging,
    handleProps: {
      onPointerDown,
      onPointerMove,
      onPointerUp: stop,
      onPointerCancel: stop,
    },
  };
}
