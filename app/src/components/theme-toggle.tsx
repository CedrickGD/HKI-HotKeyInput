import { AnimatePresence, motion } from "framer-motion";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/theme/use-theme";
import { cn } from "@/lib/utils";

export function ThemeToggle({ className }: { className?: string }) {
  const { mode, toggleMode } = useTheme();
  const isDark = mode === "dark";

  return (
    <motion.button
      type="button"
      onClick={toggleMode}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      whileTap={{ scale: 0.92 }}
      whileHover={{ scale: 1.05 }}
      transition={{ type: "spring", stiffness: 400, damping: 22 }}
      className={cn(
        "relative flex h-9 w-9 items-center justify-center rounded-full",
        "border border-border bg-card/70 backdrop-blur-sm",
        "text-foreground shadow-soft overflow-hidden",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        className,
      )}
    >
      <motion.span
        aria-hidden
        className="pointer-events-none absolute inset-0 rounded-full"
        animate={{
          background: isDark
            ? "radial-gradient(circle at 50% 50%, hsl(var(--primary)/0.22), transparent 70%)"
            : "radial-gradient(circle at 50% 50%, hsl(48 96% 60%/0.28), transparent 70%)",
        }}
        transition={{ duration: 0.5 }}
      />
      <AnimatePresence initial={false} mode="wait">
        {isDark ? (
          <motion.span
            key="moon"
            initial={{ rotate: -90, scale: 0, opacity: 0 }}
            animate={{ rotate: 0, scale: 1, opacity: 1 }}
            exit={{ rotate: 90, scale: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
            className="text-primary"
          >
            <Moon className="h-[18px] w-[18px]" strokeWidth={2} />
          </motion.span>
        ) : (
          <motion.span
            key="sun"
            initial={{ rotate: 90, scale: 0, opacity: 0 }}
            animate={{ rotate: 0, scale: 1, opacity: 1 }}
            exit={{ rotate: -90, scale: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
            className="text-amber-500"
          >
            <Sun className="h-[18px] w-[18px]" strokeWidth={2.25} />
          </motion.span>
        )}
      </AnimatePresence>
    </motion.button>
  );
}
