"use client";

import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { AnimatedNumber } from "@/components/ui/animated-number";

const Sparkline = dynamic(() => import("./sparkline").then((m) => ({ default: m.Sparkline })), {
  ssr: false,
});

export type KPIAccent = "primary" | "success" | "warning" | "purple" | "info";

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  className?: string;
  sparklineData?: { value: number }[];
  sparklineColor?: string;
  icon?: LucideIcon;
  accentColor?: KPIAccent;
  index?: number;
}

const accentMap: Record<KPIAccent, { gradient: string; ring: string; glow: string; chartVar: string }> = {
  primary: {
    gradient: "from-primary/10 via-primary/5 to-transparent",
    ring: "ring-primary/20",
    glow: "var(--chart-1)",
    chartVar: "var(--chart-1)",
  },
  success: {
    gradient: "from-chart-2/10 via-chart-2/5 to-transparent",
    ring: "ring-chart-2/20",
    glow: "var(--chart-2)",
    chartVar: "var(--chart-2)",
  },
  warning: {
    gradient: "from-chart-3/10 via-chart-3/5 to-transparent",
    ring: "ring-chart-3/20",
    glow: "var(--chart-3)",
    chartVar: "var(--chart-3)",
  },
  purple: {
    gradient: "from-chart-4/10 via-chart-4/5 to-transparent",
    ring: "ring-chart-4/20",
    glow: "var(--chart-4)",
    chartVar: "var(--chart-4)",
  },
  info: {
    gradient: "from-chart-1/10 via-chart-5/5 to-transparent",
    ring: "ring-chart-1/20",
    glow: "var(--chart-1)",
    chartVar: "var(--chart-1)",
  },
};

export function KPICard({
  title,
  value,
  subtitle,
  trend,
  className,
  sparklineData,
  sparklineColor,
  icon: Icon,
  accentColor = "primary",
  index = 0,
}: KPICardProps) {
  const accent = accentMap[accentColor];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.05, ease: "easeOut" }}
      whileHover={{ y: -2 }}
      className={className}
    >
      <Card
        variant="glass"
        style={{ "--glow-color": accent.glow } as React.CSSProperties}
        className={cn(
          "group relative h-full overflow-hidden bg-gradient-to-br",
          accent.gradient
        )}
      >
        <span
          className={cn(
            "absolute inset-x-0 top-0 h-0.5 rounded-t-xl opacity-80",
            "bg-gradient-to-r from-transparent via-current to-transparent",
            accentColor === "success" && "text-chart-2",
            accentColor === "warning" && "text-chart-3",
            accentColor === "purple" && "text-chart-4",
            accentColor === "info" && "text-chart-1",
            accentColor === "primary" && "text-primary"
          )}
        />
        <CardHeader className="relative flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
          {Icon && (
            <div
              className={cn(
                "flex h-9 w-9 items-center justify-center rounded-lg bg-white/5 transition-all group-hover:scale-110 group-hover:bg-white/10",
                "group-hover:[box-shadow:0_0_12px_-3px_var(--glow-color)]"
              )}
            >
              <Icon className="h-4 w-4 text-foreground/70 transition-colors group-hover:text-foreground" />
            </div>
          )}
        </CardHeader>
        <CardContent className="flex-1 flex flex-col justify-between">
          <div className="text-2xl font-bold tabular-nums">
            {typeof value === "number" ? <AnimatedNumber value={value} decimals={Number.isInteger(value) ? 0 : 1} /> : value}
          </div>
          {subtitle && (
            <p
              className={cn(
                "mt-1 text-xs",
                trend === "up" && "text-chart-2",
                trend === "down" && "text-destructive",
                !trend && "text-muted-foreground"
              )}
            >
              {subtitle}
            </p>
          )}
          {sparklineData && sparklineData.length > 0 && (
            <div className="mt-2">
              <Sparkline data={sparklineData} color={sparklineColor ?? accent.chartVar} />
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
