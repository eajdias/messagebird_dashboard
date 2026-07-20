"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  className?: string;
}

export function KPICard({ title, value, subtitle, trend, className }: KPICardProps) {
  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
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
      </CardContent>
    </Card>
  );
}
