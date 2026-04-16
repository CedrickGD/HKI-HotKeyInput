import * as React from "react";
import { cn } from "@/lib/utils";

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  variant?: "default" | "outline" | "muted";
};

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium font-mono tracking-wide",
        variant === "default" && "bg-primary/15 text-primary",
        variant === "outline" && "border border-border text-foreground/80",
        variant === "muted" && "bg-muted text-muted-foreground",
        className,
      )}
      {...props}
    />
  );
}
