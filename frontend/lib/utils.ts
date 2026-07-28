import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function safeNum(v: unknown, fallback = 0): number {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const n = Number(v);
    if (Number.isFinite(n)) return n;
  }
  return fallback;
}

export function formatMetric(value: number | null | undefined, decimals = 1, suffix = ""): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${value.toFixed(decimals)}${suffix}`;
}

export function ymd(d: Date): string {
  return d.toISOString().split("T")[0];
}

/** Return default billing period: 25th of previous month → 25th of current month.
 *  If today is before the 25th, both dates shift one month back. */
export function defaultPeriod(): { start: string; end: string } {
  const now = new Date();
  const day = now.getDate();
  const month = now.getMonth(); // 0-indexed
  const year = now.getFullYear();

  const endIsCurrentMonth = day >= 25;

  const endYear = endIsCurrentMonth ? year : month === 0 ? year - 1 : year;
  const endMonth = endIsCurrentMonth ? month : month === 0 ? 11 : month - 1;

  const startYear = endMonth === 0 ? endYear - 1 : endYear;
  const startMonth = endMonth === 0 ? 11 : endMonth - 1;

  return {
    start: ymd(new Date(startYear, startMonth, 25)),
    end: ymd(new Date(endYear, endMonth, 25)),
  };
}

export function downloadCsv<T extends Record<string, unknown>>(
  rows: T[],
  columns: { key: keyof T; label: string; format?: (val: T[keyof T]) => string }[],
  filename: string,
) {
  const header = columns.map((c) => c.label).join(",");
  const body = rows
    .map((row) =>
      columns
        .map((c) => {
          let val = row[c.key];
          if (c.format) return c.format(val);
          if (val == null) return "";
          const str = String(val);
          return str.includes(",") || str.includes('"') || str.includes("\n")
            ? `"${str.replace(/"/g, '""')}"`
            : str;
        })
        .join(","),
    )
    .join("\n");

  const blob = new Blob(["\uFEFF" + header + "\n" + body], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}
