"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { ExecutiveBSCResponse } from "@/types";

interface BSCExecutiveTableProps {
  data: ExecutiveBSCResponse | null;
  className?: string;
}

function safeNum(v: unknown, fallback: number | null = null): number | null {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const n = Number(v);
    if (Number.isFinite(n)) return n;
  }
  return fallback;
}

function parseMeta(meta: string | number | null | undefined): { value: number | null; type: "min" | "target" | "max" | "range" | "escalonado" | "binary" | "other" } {
  if (meta == null) return { value: null, type: "other" };
  if (typeof meta === "number") return { value: meta, type: "other" };
  const s = String(meta).trim();

  // Patterns:
  //  ">40%", "<=10%", ">=70/63/50", "150", "10", "0"
  if (s.startsWith(">=")) {
    const v = parseFloat(s.slice(2));
    return { value: Number.isFinite(v) ? v : null, type: "min" };
  }
  if (s.startsWith("<=")) {
    const v = parseFloat(s.slice(2));
    return { value: Number.isFinite(v) ? v : null, type: "max" };
  }
  if (s.startsWith(">")) {
    const v = parseFloat(s.slice(1));
    return { value: Number.isFinite(v) ? v : null, type: "min" };
  }
  if (s.startsWith("<")) {
    const v = parseFloat(s.slice(1));
    return { value: Number.isFinite(v) ? v : null, type: "max" };
  }
  if (s.includes("/")) {
    const parts = s.split("/").map((p) => parseFloat(p));
    return { value: parts.find((p) => Number.isFinite(p)) ?? null, type: "escalonado" };
  }
  const v = parseFloat(s);
  return { value: Number.isFinite(v) ? v : null, type: "target" };
}

function attainmentClass(value: number | null, meta: { value: number | null; type: ReturnType<typeof parseMeta>["type"] }): string {
  if (value == null || meta.value == null) return "";
  const ratio = value / meta.value;
  switch (meta.type) {
    case "min":
    case "target":
      if (ratio >= 1) return "text-chart-2 font-semibold";
      if (ratio >= 0.5) return "text-chart-3";
      return "text-destructive";
    case "max":
      // For "max" (lower is better): if value <= meta, green
      if (value <= meta.value) return "text-chart-2 font-semibold";
      if (value <= meta.value * 1.5) return "text-chart-3";
      return "text-destructive";
    case "escalonado":
      // Value is the highest tier met
      if (value >= meta.value) return "text-chart-2 font-semibold";
      if (value >= meta.value * 0.5) return "text-chart-3";
      return "text-destructive";
    default:
      return "";
  }
}

interface BSCRow {
  name: string;
  meta: string | number | null;
  type: string;
  values: (string | number | null)[];
}

function buildRows(
  kpiConfig: Record<string, unknown> | null,
  dataRows: (string | number | null)[][] | null
): BSCRow[] {
  if (!kpiConfig || !dataRows) return [];
  const configArr = (kpiConfig.t1 as Array<Record<string, unknown>>) || [];
  return dataRows.map((row, i) => {
    const meta = (row[0] as string) || "";
    const cfg = configArr[i] || {};
    return {
      name: meta,
      meta: (cfg.meta as string | number | null) ?? null,
      type: (cfg.tipo as string) ?? "",
      values: row.slice(1),
    };
  });
}

export function BSCExecutiveTable({ data, className }: BSCExecutiveTableProps) {
  const t1Rows = useMemo(
    () => buildRows(data?.kpi_config as Record<string, unknown> | null, data?.data_t1 ?? null),
    [data]
  );
  const t2Rows = useMemo(
    () => buildRows(
      data?.kpi_config ? { t2: (data.kpi_config as Record<string, unknown>).t2 } : null,
      data?.data_t2 ?? null
    ),
    [data]
  );

  if (!data || data.header.length === 0) {
    return (
      <Card variant="glass" className={className}>
        <CardHeader>
          <CardTitle className="text-base">BSC — {data?.group || "Suporte Tecnico"}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Sem dados para o grupo no período
          </p>
        </CardContent>
      </Card>
    );
  }

  const agentColumns = data.header.slice(1);
  const total = data.total_chats;

  const renderRow = (row: BSCRow, idx: number) => {
    const meta = parseMeta(row.meta);
    return (
      <tr key={idx} className="border-b border-white/5 transition-colors hover:bg-white/5">
        <td className="px-3 py-2 text-sm font-medium">{row.name}</td>
        <td className="px-3 py-2 text-center text-xs text-muted-foreground tabular-nums">
          {row.meta != null ? String(row.meta) : "—"}
        </td>
        {row.values.map((v, ci) => {
          const num = safeNum(v);
          const cls = attainmentClass(num, meta);
          return (
            <td
              key={ci}
              className={cn("px-3 py-2 text-center text-sm tabular-nums", cls)}
            >
              {v != null ? String(v) : "—"}
            </td>
          );
        })}
      </tr>
    );
  };

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">BSC — {data.group}</CardTitle>
          <div className="text-xs text-muted-foreground">
            Total no grupo: <span className="font-semibold text-foreground">{total}</span> chats
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {t1Rows.length > 0 && (
          <div className="mb-4">
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              T1 — Métricas Principais
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="px-3 py-2 text-left font-medium text-muted-foreground">Métrica</th>
                    <th className="px-3 py-2 text-center font-medium text-muted-foreground">Meta</th>
                    {agentColumns.map((a) => (
                      <th
                        key={a}
                        className="px-3 py-2 text-center font-medium text-muted-foreground"
                      >
                        {a}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>{t1Rows.map((r, i) => renderRow(r, i))}</tbody>
              </table>
            </div>
          </div>
        )}
        {t2Rows.length > 0 && (
          <div>
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              T2 — Avaliações Extras
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="px-3 py-2 text-left font-medium text-muted-foreground">Métrica</th>
                    <th className="px-3 py-2 text-center font-medium text-muted-foreground">Meta</th>
                    {agentColumns.map((a) => (
                      <th
                        key={a}
                        className="px-3 py-2 text-center font-medium text-muted-foreground"
                      >
                        {a}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>{t2Rows.map((r, i) => renderRow(r, i))}</tbody>
              </table>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
