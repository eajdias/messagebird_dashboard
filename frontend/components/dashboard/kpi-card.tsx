"use client";

import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { AnimatedNumber } from "@/components/ui/animated-number";

const Sparkline = dynamic(() => import("./sparkline").then((m) => ({ default: m.Sparkline })), {
  ssr: false,
});

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  className?: string;
  sparklineData?: { value: number }[];
  sparklineColor?: string;
}

export function KPICard({ title, value, subtitle, trend, className, sparklineData, sparklineColor }: KPICardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <Card className={cn("group transition-shadow hover:shadow-md", className)}>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col justify-between">
          <div className="text-2xl font-bold tabular-nums">
            {typeof value === "number" ? <AnimatedNumber value={value} decimals={Number.isInteger(value) ? 0 : 1} /> : value}
          </div>
          {subtitle && (
            <p
              className={cn(
                "mt-1 text-xs",
                trend === "up" && "text-green-600 dark:text-green-400",
                trend === "down" && "text-red-600 dark:text-red-400",
                !trend && "text-muted-foreground"
              )}
            >
              {subtitle}
            </p>
          )}
          {sparklineData && sparklineData.length > 0 && (
            <div className="mt-2">
              <Sparkline data={sparklineData} color={sparklineColor ?? "#3b82f6"} />
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
