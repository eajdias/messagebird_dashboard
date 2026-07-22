"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { cn } from "@/lib/utils";

export interface TabOption<T extends string> {
  value: T;
  label: string;
}

interface TabsProps<T extends string> {
  value: T;
  onChange: (value: T) => void;
  options: TabOption<T>[];
  paramName?: string;
  size?: "sm" | "md";
  className?: string;
}

export function Tabs<T extends string>({
  value,
  onChange,
  options,
  paramName = "tab",
  size = "md",
  className,
}: TabsProps<T>) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleChange = useCallback(
    (next: T) => {
      if (next === value) return;
      onChange(next);
      const params = new URLSearchParams(searchParams?.toString() || "");
      params.set(paramName, next);
      router.replace(`?${params.toString()}`, { scroll: false });
    },
    [onChange, value, router, searchParams, paramName]
  );

  return (
    <div
      role="tablist"
      className={cn(
        "inline-flex items-center gap-0.5 rounded-lg border border-white/10 bg-white/5 p-0.5 backdrop-blur-sm",
        className
      )}
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => handleChange(opt.value)}
            className={cn(
              "rounded-md font-medium transition-all",
              size === "sm" ? "h-7 px-2.5 text-xs" : "h-9 px-3.5 text-sm",
              active
                ? "bg-primary/20 text-foreground shadow-[0_0_8px_-2px_var(--primary)]"
                : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
            )}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

export function readTabFromQuery<T extends string>(
  searchParams: URLSearchParams | undefined,
  paramName: string,
  options: TabOption<T>[],
  fallback: T
): T {
  const raw = searchParams?.get(paramName);
  if (raw && options.some((o) => o.value === raw)) {
    return raw as T;
  }
  return fallback;
}
