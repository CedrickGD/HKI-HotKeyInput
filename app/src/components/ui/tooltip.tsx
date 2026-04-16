import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";

type TooltipSide = "top" | "bottom" | "left" | "right";

type TooltipProps = {
  content: React.ReactNode;
  children: React.ReactNode;
  side?: TooltipSide;
  delay?: number;
  className?: string;
};

export function Tooltip({
  content,
  children,
  side = "bottom",
  delay = 250,
  className,
}: TooltipProps) {
  const [open, setOpen] = React.useState(false);
  const timerRef = React.useRef<number | null>(null);

  const show = React.useCallback(() => {
    if (timerRef.current !== null) window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => setOpen(true), delay);
  }, [delay]);

  const hide = React.useCallback(() => {
    if (timerRef.current !== null) window.clearTimeout(timerRef.current);
    timerRef.current = null;
    setOpen(false);
  }, []);

  React.useEffect(() => {
    return () => {
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
    };
  }, []);

  const sideClass: Record<TooltipSide, string> = {
    top: "bottom-full left-1/2 mb-2 -translate-x-1/2",
    bottom: "top-full left-1/2 mt-2 -translate-x-1/2",
    left: "right-full top-1/2 mr-2 -translate-y-1/2",
    right: "left-full top-1/2 ml-2 -translate-y-1/2",
  };

  const offset: Record<TooltipSide, { x: number; y: number }> = {
    top: { x: 0, y: 4 },
    bottom: { x: 0, y: -4 },
    left: { x: 4, y: 0 },
    right: { x: -4, y: 0 },
  };

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      <AnimatePresence>
        {open && (
          <motion.span
            role="tooltip"
            initial={{ opacity: 0, ...offset[side] }}
            animate={{ opacity: 1, x: 0, y: 0 }}
            exit={{ opacity: 0, ...offset[side] }}
            transition={{ duration: 0.12, ease: "easeOut" }}
            className={cn(
              "pointer-events-none absolute z-50 whitespace-nowrap rounded-md px-2 py-1 text-[11px] font-medium",
              "bg-foreground text-background shadow-soft",
              sideClass[side],
              className,
            )}
          >
            {content}
          </motion.span>
        )}
      </AnimatePresence>
    </span>
  );
}
