import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "success" | "warning" | "outline"
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        {
          "border-border bg-secondary text-foreground": variant === "default",
          "border-border bg-muted text-foreground": variant === "secondary",
          "border-destructive bg-destructive/20 text-destructive": variant === "destructive",
          "border-success bg-success/20 text-success": variant === "success",
          "border-warning bg-warning/20 text-warning": variant === "warning",
          "border-border text-foreground": variant === "outline",
        },
        className
      )}
      {...props}
    />
  )
}

export { Badge }

