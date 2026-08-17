"use client";

import { useEffect, useState } from "react";
import { Check, ChevronDown, UserCircle2, X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { AgentItem } from "@/types";

interface AgentMultiSelectProps {
  agents: AgentItem[];
  selected: string[];
  onChange: (next: string[]) => void;
  loading?: boolean;
}

export function AgentMultiSelect({
  agents,
  selected,
  onChange,
  loading,
}: AgentMultiSelectProps) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  const toggle = (name: string) => {
    if (selected.includes(name)) {
      onChange(selected.filter((n) => n !== name));
    } else {
      onChange([...selected, name]);
    }
  };

  const clear = () => onChange([]);

  const label =
    selected.length === 0
      ? "Todos os agentes"
      : selected.length === 1
        ? selected[0]
        : `${selected.length} agentes`;

  return (
    <div className="relative">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen((p) => !p)}
        className="h-9 gap-2 border-white/10 bg-white/5 backdrop-blur-sm"
        aria-haspopup="listbox"
        aria-expanded={open}
        disabled={loading}
      >
        <UserCircle2 className="h-4 w-4" />
        <span className="hidden sm:inline max-w-[180px] truncate">{label}</span>
        {selected.length > 0 && (
          <span
            role="button"
            tabIndex={0}
            onClick={(e) => {
              e.stopPropagation();
              clear();
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.stopPropagation();
                clear();
              }
            }}
            className="ml-1 flex h-5 w-5 items-center justify-center rounded-full bg-white/10 text-xs hover:bg-white/20"
            aria-label="Limpar seleção"
          >
            <X className="h-3 w-3" />
          </span>
        )}
        <ChevronDown className="h-3 w-3 opacity-60" />
      </Button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          <Card
            variant="glass"
            className="absolute right-0 top-full z-50 mt-1 w-80 max-h-96 overflow-hidden p-0"
          >
            <CardHeader className="border-b border-white/5 py-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Selecionar agentes</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clear}
                  disabled={selected.length === 0}
                  className="h-7 text-xs"
                >
                  Limpar
                </Button>
              </div>
            </CardHeader>
            <CardContent className="max-h-72 overflow-y-auto p-1">
              {agents.length === 0 ? (
                <p className="p-4 text-center text-sm text-muted-foreground">
                  Nenhum agente disponível
                </p>
              ) : (
                <ul role="listbox" className="space-y-0.5">
                  {agents.map((a) => {
                    const isSelected = selected.includes(a.name);
                    return (
                      <li key={a.bird_id}>
                        <button
                          type="button"
                          role="option"
                          aria-selected={isSelected}
                          onClick={() => toggle(a.name)}
                          className={cn(
                            "flex w-full items-center justify-between gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors",
                            isSelected
                              ? "bg-primary/15 text-foreground"
                              : "hover:bg-white/5"
                          )}
                        >
                          <div className="min-w-0 flex-1">
                            <p className="truncate font-medium">{a.name}</p>
                            {a.group && (
                              <p className="truncate text-xs text-muted-foreground">
                                {a.group}
                              </p>
                            )}
                          </div>
                          <div
                            className={cn(
                              "flex h-4 w-4 shrink-0 items-center justify-center rounded border",
                              isSelected
                                ? "border-primary bg-primary text-primary-foreground"
                                : "border-white/20"
                            )}
                          >
                            {isSelected && <Check className="h-3 w-3" />}
                          </div>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
