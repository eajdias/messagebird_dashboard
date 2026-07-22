"use client";

import { useEffect, useState } from "react";
import { Check, ChevronDown, Building2, X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import api from "@/lib/api";

interface DeptItem {
  dept_id: number;
  label: string;
}

interface DepartmentMultiSelectProps {
  selected: string[];
  onChange: (next: string[]) => void;
}

export function DepartmentMultiSelect({ selected, onChange }: DepartmentMultiSelectProps) {
  const [open, setOpen] = useState(false);
  const [depts, setDepts] = useState<DeptItem[]>([]);

  useEffect(() => {
    api
      .get<{ departments: DeptItem[] }>("/api/v1/admin/departments")
      .then((r) => setDepts(r.data.departments))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  const toggle = (label: string) => {
    if (selected.includes(label)) {
      onChange(selected.filter((n) => n !== label));
    } else {
      onChange([...selected, label]);
    }
  };

  const clear = () => onChange([]);

  const label =
    selected.length === 0
      ? "Todos os departamentos"
      : selected.length === 1
        ? selected[0]
        : `${selected.length} departamentos`;

  return (
    <div className="relative">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen((p) => !p)}
        className="h-9 gap-2 border-white/10 bg-white/5 backdrop-blur-sm"
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <Building2 className="h-4 w-4" />
        <span className="hidden sm:inline max-w-[200px] truncate">{label}</span>
        {selected.length > 0 && (
          <span
            role="button"
            tabIndex={0}
            onClick={(e) => {
              e.stopPropagation();
              clear();
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
            className="absolute right-0 top-full z-50 mt-1 w-72 max-h-80 overflow-hidden p-0"
          >
            <CardHeader className="border-b border-white/5 py-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Selecionar depto.</CardTitle>
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
            <CardContent className="max-h-60 overflow-y-auto p-1">
              {depts.length === 0 ? (
                <p className="p-4 text-center text-sm text-muted-foreground">
                  Nenhum departamento disponível
                </p>
              ) : (
                <ul role="listbox" className="space-y-0.5">
                  {depts.map((d) => {
                    const isSelected = selected.includes(d.label);
                    return (
                      <li key={d.dept_id}>
                        <button
                          type="button"
                          role="option"
                          aria-selected={isSelected}
                          onClick={() => toggle(d.label)}
                          className={cn(
                            "flex w-full items-center justify-between gap-2 rounded-md px-3 py-2.5 text-left text-sm transition-colors",
                            isSelected
                              ? "bg-primary/15 text-foreground"
                              : "hover:bg-white/5"
                          )}
                        >
                          <span className="truncate font-medium">{d.label}</span>
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
