"use client";

import { Calendar } from "lucide-react";
import { cn } from "@/lib/utils";

interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onChange: (start: string, end: string) => void;
  className?: string;
}

export function DateRangePicker({ startDate, endDate, onChange, className }: DateRangePickerProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-2 py-1",
        className,
      )}
    >
      <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
      <input
        type="date"
        value={startDate}
        onChange={(e) => onChange(e.target.value, endDate)}
        className="h-6 w-[130px] bg-transparent text-xs text-foreground outline-none [color-scheme:dark]"
      />
      <span className="text-[10px] text-muted-foreground">→</span>
      <input
        type="date"
        value={endDate}
        onChange={(e) => onChange(startDate, e.target.value)}
        className="h-6 w-[130px] bg-transparent text-xs text-foreground outline-none [color-scheme:dark]"
      />
    </div>
  );
}
