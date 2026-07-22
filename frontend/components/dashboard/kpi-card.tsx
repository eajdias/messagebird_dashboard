"use client";

import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

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
    <Card className={cn("flex flex-col", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-between">
        <div className="text-2xl font-bold">{value}</div>
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
  );
}
