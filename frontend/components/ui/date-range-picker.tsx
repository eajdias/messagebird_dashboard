"use client";

import { useEffect, useRef, useState } from "react";
import { Calendar, Check, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onChange: (start: string, end: string) => void;
  onConfirm?: (start: string, end: string) => void;
  hasPendingChanges?: boolean;
  className?: string;
}

interface DatePreset {
  label: string;
  getRange: () => { start: string; end: string };
}

function isValidDate(s: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(s) && !isNaN(Date.parse(s));
}

function ymd(d: Date): string {
  return d.toISOString().split("T")[0];
}

function todayYmd(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function startOfMonth(): string {
  const now = new Date();
  return ymd(new Date(now.getFullYear(), now.getMonth(), 1));
}

function endOfMonth(): string {
  const now = new Date();
  const last = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  const today = todayYmd();
  const end = ymd(last);
  return end > today ? today : end;
}

function startOfLastMonth(): string {
  const now = new Date();
  return ymd(new Date(now.getFullYear(), now.getMonth() - 1, 1));
}

function endOfLastMonth(): string {
  const now = new Date();
  return ymd(new Date(now.getFullYear(), now.getMonth(), 0));
}

const MAX_RANGE_DAYS = 3650;

const DATE_PRESETS: DatePreset[] = [
  { label: "Mês atual", getRange: () => ({ start: startOfMonth(), end: endOfMonth() }) },
  { label: "Mês anterior", getRange: () => ({ start: startOfLastMonth(), end: endOfLastMonth() }) },
  { label: "Ano atual", getRange: () => ({ start: `${new Date().getFullYear()}-01-01`, end: todayYmd() }) },
  { label: "Últimos 2 anos", getRange: () => ({ start: `${new Date().getFullYear() - 1}-01-01`, end: todayYmd() }) },
];

export function DateRangePicker({
  startDate,
  endDate,
  onChange,
  onConfirm,
  hasPendingChanges = false,
  className,
}: DateRangePickerProps) {
  const [localStart, setLocalStart] = useState(startDate);
  const [localEnd, setLocalEnd] = useState(endDate);

  // Sync local state when props change from outside (e.g. preset applied in parent)
  const prevStartRef = useRef(startDate);
  const prevEndRef = useRef(endDate);
  useEffect(() => {
    if (prevStartRef.current !== startDate || prevEndRef.current !== endDate) {
      prevStartRef.current = startDate;
      prevEndRef.current = endDate;
      setLocalStart(startDate);
      setLocalEnd(endDate);
    }
  }, [startDate, endDate]);

  const today = new Date().toISOString().slice(0, 10);

  const handleStartChange = (value: string) => {
    if (!isValidDate(value)) return;
    if (value > today) return;
    if (isValidDate(localEnd) && value > localEnd) {
      setLocalStart(value);
      setLocalEnd(value);
    } else {
      setLocalStart(value);
    }
  };

  const handleEndChange = (value: string) => {
    if (!isValidDate(value)) return;
    if (value > today) return;
    if (isValidDate(localStart) && value < localStart) {
      setLocalEnd(localStart);
      setLocalStart(value);
    } else {
      setLocalEnd(value);
    }
  };

  const handlePreset = (preset: DatePreset) => {
    const range = preset.getRange();
    const diff = (new Date(range.end).getTime() - new Date(range.start).getTime()) / (1000 * 60 * 60 * 24);
    if (diff > MAX_RANGE_DAYS) {
      window.alert("Período máximo permitido é de 10 anos");
      return;
    }
    setLocalStart(range.start);
    setLocalEnd(range.end);
    (onConfirm ?? onChange)(range.start, range.end);
  };

  const handleConfirm = () => {
    const diff = (new Date(localEnd).getTime() - new Date(localStart).getTime()) / (1000 * 60 * 60 * 24);
    if (diff > MAX_RANGE_DAYS) {
      window.alert("Período máximo permitido é de 10 anos");
      return;
    }
    (onConfirm ?? onChange)(localStart, localEnd);
  };

  const handleClear = () => {
    const now = new Date();
    const defaultStart = ymd(new Date(now.getFullYear(), now.getMonth() - 1, 25));
    const defaultEnd = ymd(new Date(now.getFullYear(), now.getMonth(), 25));
    setLocalStart(defaultStart);
    setLocalEnd(defaultEnd);
    (onConfirm ?? onChange)(defaultStart, defaultEnd);
  };

  const isDirty = localStart !== startDate || localEnd !== endDate;

  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <div className="flex items-center gap-1.5">
        {DATE_PRESETS.map((preset) => (
          <button
            key={preset.label}
            onClick={() => handlePreset(preset)}
            className="rounded-md border border-border bg-card px-2 py-0.5 text-[10px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            {preset.label}
          </button>
        ))}
      </div>
      <div className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-2 py-1">
        <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
        <input
          type="date"
          value={localStart}
          max={today}
          onChange={(e) => handleStartChange(e.target.value)}
          className="h-6 w-[130px] bg-transparent text-xs text-foreground outline-none [color-scheme:dark]"
        />
        <span className="text-[10px] text-muted-foreground">→</span>
        <input
          type="date"
          value={localEnd}
          max={today}
          onChange={(e) => handleEndChange(e.target.value)}
          className="h-6 w-[130px] bg-transparent text-xs text-foreground outline-none [color-scheme:dark]"
        />
        {isDirty && (
          <Button
            size="icon"
            variant="ghost"
            onClick={handleConfirm}
            className="h-5 w-5 text-green-500 hover:text-green-400"
            title="Confirmar período"
          >
            <Check className="h-3 w-3" />
          </Button>
        )}
        <Button
          size="icon"
          variant="ghost"
          onClick={handleClear}
          className="h-5 w-5 text-muted-foreground hover:text-foreground"
          title="Voltar ao período padrão"
        >
          <X className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );
}
