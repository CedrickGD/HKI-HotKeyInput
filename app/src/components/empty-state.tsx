import { motion, useReducedMotion } from "framer-motion";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";

export function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <motion.div
      key="empty"
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
      className="flex h-full flex-col items-center justify-center gap-5 p-8 text-center"
    >
      <KeyboardArt />
      <div className="max-w-sm">
        <h3 className="text-lg font-semibold tracking-tight">
          Your hotkey workspace is empty
        </h3>
        <p className="mt-1.5 text-sm text-muted-foreground">
          Create a preset to bind text and placeholders to a global shortcut.
          Press the hotkey anywhere to paste the resolved snippet instantly.
        </p>
      </div>
      <Button onClick={onCreate}>
        <Plus className="h-4 w-4" />
        Create your first preset
      </Button>
    </motion.div>
  );
}

function KeyboardArt() {
  const reduce = useReducedMotion();
  return (
    <motion.svg
      width="160"
      height="120"
      viewBox="0 0 160 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      role="presentation"
      initial={{ scale: 0.96, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 220, damping: 20, delay: 0.05 }}
    >
      <defs>
        <linearGradient id="kbd-body" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="hsl(var(--card))" stopOpacity="0.95" />
          <stop offset="100%" stopColor="hsl(var(--muted))" stopOpacity="0.85" />
        </linearGradient>
        <linearGradient id="kbd-glow" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0.25" />
          <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0" />
        </linearGradient>
      </defs>

      <motion.ellipse
        cx="80"
        cy="92"
        rx="58"
        ry="6"
        fill="hsl(var(--foreground))"
        opacity="0.08"
        animate={reduce ? { scaleX: 1 } : { scaleX: [1, 1.04, 1] }}
        transition={
          reduce
            ? { duration: 0 }
            : { duration: 3.2, repeat: Infinity, ease: "easeInOut" }
        }
      />

      <motion.g
        animate={reduce ? { y: 0 } : { y: [0, -2, 0] }}
        transition={
          reduce
            ? { duration: 0 }
            : { duration: 3.2, repeat: Infinity, ease: "easeInOut" }
        }
      >
        <rect
          x="16"
          y="34"
          width="128"
          height="54"
          rx="10"
          fill="url(#kbd-body)"
          stroke="hsl(var(--border))"
          strokeWidth="1"
        />
        <rect
          x="16"
          y="34"
          width="128"
          height="54"
          rx="10"
          fill="url(#kbd-glow)"
        />

        {/* Top row keys */}
        <g fill="hsl(var(--background))" stroke="hsl(var(--border))" strokeWidth="0.75">
          <rect x="24" y="42" width="14" height="14" rx="3" />
          <rect x="42" y="42" width="14" height="14" rx="3" />
          <rect x="60" y="42" width="14" height="14" rx="3" />
          <rect x="78" y="42" width="14" height="14" rx="3" />
          <rect x="96" y="42" width="14" height="14" rx="3" />
          <rect x="114" y="42" width="22" height="14" rx="3" />
        </g>

        {/* Middle row */}
        <g fill="hsl(var(--background))" stroke="hsl(var(--border))" strokeWidth="0.75">
          <rect x="24" y="60" width="20" height="14" rx="3" />
          <rect x="48" y="60" width="14" height="14" rx="3" />
          <rect x="66" y="60" width="14" height="14" rx="3" />
          <rect x="84" y="60" width="14" height="14" rx="3" />
          <rect x="102" y="60" width="14" height="14" rx="3" />
          <rect
            x="120"
            y="60"
            width="16"
            height="14"
            rx="3"
            fill="hsl(var(--primary))"
            opacity="0.22"
          />
        </g>

        {/* Spacebar */}
        <rect
          x="44"
          y="78"
          width="72"
          height="6"
          rx="2"
          fill="hsl(var(--background))"
          stroke="hsl(var(--border))"
          strokeWidth="0.75"
        />
      </motion.g>

      {/* Sparkles */}
      <motion.g
        animate={reduce ? { rotate: 0 } : { rotate: [0, 8, -6, 0] }}
        transition={
          reduce
            ? { duration: 0 }
            : { duration: 5, repeat: Infinity, ease: "easeInOut" }
        }
        style={{ transformOrigin: "130px 22px" }}
      >
        <path
          d="M130 14 L132 20 L138 22 L132 24 L130 30 L128 24 L122 22 L128 20 Z"
          fill="hsl(var(--primary))"
          opacity="0.9"
        />
      </motion.g>
      <motion.g
        animate={
          reduce
            ? { scale: 1, opacity: 0.8 }
            : { scale: [0.9, 1.1, 0.9], opacity: [0.6, 1, 0.6] }
        }
        transition={
          reduce
            ? { duration: 0 }
            : { duration: 2.4, repeat: Infinity, ease: "easeInOut" }
        }
        style={{ transformOrigin: "28px 20px" }}
      >
        <circle cx="28" cy="20" r="2.4" fill="hsl(var(--primary))" />
      </motion.g>
      <motion.g
        animate={
          reduce
            ? { scale: 1, opacity: 0.7 }
            : { scale: [1, 1.25, 1], opacity: [0.5, 0.95, 0.5] }
        }
        transition={
          reduce
            ? { duration: 0 }
            : { duration: 3, repeat: Infinity, ease: "easeInOut", delay: 0.6 }
        }
        style={{ transformOrigin: "146px 70px" }}
      >
        <circle cx="146" cy="70" r="2" fill="hsl(var(--primary))" />
      </motion.g>
    </motion.svg>
  );
}
