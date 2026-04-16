import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import { toastStore, type Toast, type ToastKind } from "@/lib/toast-store";
import { cn } from "@/lib/utils";

const ICONS: Record<ToastKind, React.ComponentType<{ className?: string }>> = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

const ACCENTS: Record<ToastKind, string> = {
  success: "text-emerald-500",
  error: "text-destructive",
  info: "text-primary",
};

export function Toaster() {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  React.useEffect(() => toastStore.subscribe(setToasts), []);

  return (
    <div className="pointer-events-none fixed right-3 top-3 z-[60] flex w-[320px] max-w-[calc(100vw-1.5rem)] flex-col gap-2">
      <AnimatePresence initial={false}>
        {toasts.map((t) => {
          const Icon = ICONS[t.kind];
          return (
            <motion.div
              key={t.id}
              layout
              initial={{ opacity: 0, x: 24, scale: 0.98 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 24, scale: 0.98 }}
              transition={{ type: "spring", stiffness: 340, damping: 28 }}
              role="status"
              aria-live="polite"
              className={cn(
                "pointer-events-auto overflow-hidden rounded-lg border border-border/80 bg-card/95 shadow-soft backdrop-blur-md",
                "flex gap-3 px-3.5 py-3",
              )}
            >
              <Icon className={cn("mt-0.5 h-4 w-4 shrink-0", ACCENTS[t.kind])} />
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium text-foreground">
                  {t.title}
                </div>
                {t.description ? (
                  <div className="mt-0.5 text-xs text-muted-foreground">
                    {t.description}
                  </div>
                ) : null}
                {t.action ? (
                  <div className="mt-1.5">
                    <button
                      type="button"
                      onClick={() => {
                        t.action?.onClick();
                        toastStore.dismiss(t.id);
                      }}
                      className="inline-flex h-6 items-center rounded-sm border border-border/70 bg-background/60 px-2 text-[11px] font-medium text-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      {t.action.label}
                    </button>
                  </div>
                ) : null}
              </div>
              <button
                type="button"
                onClick={() => toastStore.dismiss(t.id)}
                aria-label="Dismiss"
                className="-mr-1 flex h-5 w-5 shrink-0 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
