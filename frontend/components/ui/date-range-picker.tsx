"use client";

import { Calendar } from "lucide-react";
import { cn } from "@/lib/utils";

interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onChange: (start: string, end: string) => void;
  className?: string;
}

function isValidDate(s: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(s) && !isNaN(Date.parse(s));
}

export function DateRangePicker({ startDate, endDate, onChange, className }: DateRangePickerProps) {
  const handleStartChange = (value: string) => {
    if (!isValidDate(value)) return;
    if (isValidDate(endDate) && value > endDate) {
      onChange(value, value);
    } else {
      onChange(value, endDate);
    }
  };

  const handleEndChange = (value: string) => {
    if (!isValidDate(value)) return;
    if (isValidDate(startDate) && value < startDate) {
      onChange(value, startDate);
    } else {
      onChange(startDate, value);
    }
  };

  const today = new Date().toISOString().slice(0, 10);

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
        max={today}
        onChange={(e) => handleStartChange(e.target.value)}
        className="h-6 w-[130px] bg-transparent text-xs text-foreground outline-none [color-scheme:dark]"
      />
      <span className="text-[10px] text-muted-foreground">→</span>
      <input
        type="date"
        value={endDate}
        max={today}
        onChange={(e) => handleEndChange(e.target.value)}
        className="h-6 w-[130px] bg-transparent text-xs text-foreground outline-none [color-scheme:dark]"
      />
    </div>
  );
}
