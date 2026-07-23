"use client";

import { useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BSCMetricRow, BSCScorecardResponse } from "@/types";
import { Input } from "@/components/ui/input";

interface Props {
  data: BSCScorecardResponse;
  onSaveManual: (agentName: string, metricName: string, value: number) => Promise<void>;
}

export function BSCScorecardTable({ data, onSaveManual }: Props) {
  if (!data.has_config) return null;

  return (
    <div className="space-y-8">
      {data.categories.map((cat) => (
        <BSCCategorySection
          key={cat.name}
          categoryName={cat.name}
          metrics={cat.metrics}
          agents={data.agents}
          onSaveManual={onSaveManual}
        />
      ))}
      {data.penalidades.length > 0 && (
        <BSCCategorySection
          key="penalidades"
          categoryName="Penalidades"
          metrics={data.penalidades}
          agents={data.agents}
          onSaveManual={onSaveManual}
          isPenalidade
        />
      )}
    </div>
  );
}

function BSCCategorySection({
  categoryName,
  metrics,
  agents,
  onSaveManual,
  isPenalidade,
}: {
  categoryName: string;
  metrics: BSCMetricRow[];
  agents: string[];
  onSaveManual: (agentName: string, metricName: string, value: number) => Promise<void>;
  isPenalidade?: boolean;
}) {
  const t2Label = "Updates, Treinamentos e Tarefas";
  const isT2 = categoryName === t2Label;

  return (
    <Card>
      <CardHeader className="py-3">
        <CardTitle className="text-base font-semibold tracking-tight">{categoryName}</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="sticky left-0 bg-muted/50 px-3 py-2 text-left font-medium">
                  Métrica
                </th>
                <th className="px-3 py-2 text-left font-medium w-16">Meta</th>
                <th className="px-3 py-2 text-left font-medium w-14">Peso</th>
                <th className="px-3 py-2 text-left font-medium w-20">Tipo</th>
                {agents.map((agent) => (
                  <th key={agent + "-val"} className="px-2 py-2 text-center font-medium min-w-[80px]">
                    <div className="truncate max-w-[100px]" title={agent}>
                      {agent.split(" ").slice(0, 2).join(" ")}
                    </div>
                    <div className="flex text-[10px] text-muted-foreground font-normal mt-0.5 justify-center gap-1">
                      <span>Dado</span>
                      <span>KPI</span>
                    </div>
                  </th>
                ))}
                {isT2 && <th className="px-2 py-2 text-center font-medium w-16">Total</th>}
              </tr>
            </thead>
            <tbody>
              {metrics.map((metric, mi) => (
                <BSCMetricRowComponent
                  key={metric.name}
                  metric={metric}
                  agents={agents}
                  onSaveManual={onSaveManual}
                  isLast={mi === metrics.length - 1}
                  showTotal={isT2}
                />
              ))}

              {/* T2 total row */}
              {isT2 && agents.length > 0 && (
                <tr className="border-t-2 bg-muted/30 font-semibold">
                  <td className="px-3 py-2" colSpan={4}>
                    Tarefas (Total)
                  </td>
                  {agents.map((agent) => {
                    const totalKpi = metrics.reduce((sum, m) => {
                      const ag = m.per_agent.find((a) => a.agent_name === agent);
                      return sum + (ag?.kpi_score ?? 0);
                    }, 0);
                    return (
                      <td key={agent} className="px-2 py-2 text-center" colSpan={1}>
                        <div className="flex justify-center gap-4">
                          <span className="text-primary font-bold">{totalKpi.toFixed(1)}</span>
                        </div>
                      </td>
                    );
                  })}
                  <td className="px-2 py-2 text-center font-bold text-primary">
                    {metrics.reduce((sum, m) => {
                      const vals = m.per_agent.map((a) => a.kpi_score ?? 0);
                      return sum + vals.reduce((a, b) => a + b, 0);
                    }, 0).toFixed(1)}
                  </td>
                </tr>
              )}

              {/* TOTAL KPI row (only for t1 categories, NOT t2) */}
              {!isT2 && !isPenalidade && agents.length > 0 && (
                <tr className="border-t-2 border-primary/30 bg-primary/5 font-bold">
                  <td className="px-3 py-2 text-primary" colSpan={4}>
                    TOTAL KPI
                  </td>
                  {agents.map((agent) => {
                    const totalKpi = metrics.reduce((sum, m) => {
                      const ag = m.per_agent.find((a) => a.agent_name === agent);
                      return sum + (ag?.kpi_score ?? 0);
                    }, 0);
                    return (
                      <td key={agent + "-total"} className="px-2 py-2 text-center" colSpan={1}>
                        <span className="text-primary font-bold">{totalKpi.toFixed(1)}</span>
                      </td>
                    );
                  })}
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function BSCMetricRowComponent({
  metric,
  agents,
  onSaveManual,
  isLast,
  showTotal,
}: {
  metric: BSCMetricRow;
  agents: string[];
  onSaveManual: (agentName: string, metricName: string, value: number) => Promise<void>;
  isLast: boolean;
  showTotal?: boolean;
}) {
  return (
    <tr className={cn("border-b border-border/40 hover:bg-muted/30 transition-colors", isLast && "border-b-2")}>
      <td className="sticky left-0 bg-background px-3 py-2 font-medium" title={metric.description || undefined}>
        <div>{metric.name}</div>
        {metric.description && (
          <div className="text-[10px] text-muted-foreground font-normal leading-tight max-w-[240px]">
            {metric.description}
          </div>
        )}
      </td>
      <td className="px-3 py-2 text-center text-muted-foreground text-xs">{metric.meta}</td>
      <td className="px-3 py-2 text-center text-muted-foreground text-xs">{metric.peso}</td>
      <td className="px-3 py-2 text-center text-muted-foreground text-[10px]">
        {TIPO_LABELS[metric.tipo] || metric.tipo}
      </td>
      {agents.map((agent) => {
        const agentVal = metric.per_agent.find((a) => a.agent_name === agent);
        return (
          <BSCAgentCell
            key={agent}
            agentName={agent}
            agentValue={agentVal}
            metricName={metric.name}
            isManual={metric.is_manual}
            onSaveManual={onSaveManual}
          />
        );
      })}
      {showTotal && (
        <td className="px-2 py-2 text-center font-medium text-primary">
          {metric.per_agent.reduce((sum, a) => sum + (a.kpi_score ?? 0), 0).toFixed(1)}
        </td>
      )}
    </tr>
  );
}

function BSCAgentCell({
  agentName,
  agentValue,
  metricName,
  isManual,
  onSaveManual,
}: {
  agentName: string;
  agentValue: { agent_name: string; raw_value: number | null; kpi_score: number | null; is_manual: boolean } | undefined;
  metricName: string;
  isManual: boolean;
  onSaveManual: (agent: string, metric: string, value: number) => Promise<void>;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [editing, setEditing] = useState(false);
  const [localVal, setLocalVal] = useState("");

  const rawValue = agentValue?.raw_value;
  const kpiScore = agentValue?.kpi_score;

  const handleStartEdit = () => {
    if (!isManual) return;
    setLocalVal(rawValue != null ? String(rawValue) : "");
    setEditing(true);
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const handleSave = async () => {
    const val = parseFloat(localVal.replace(",", "."));
    if (!isNaN(val)) {
      await onSaveManual(agentName, metricName, val);
    }
    setEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSave();
    if (e.key === "Escape") setEditing(false);
  };

  const fmt = (v: number | null | undefined) => (v != null ? String(v) : "—");
  const kpiFmt = (v: number | null | undefined) => (v != null ? v.toFixed(1) : "—");
  const kpiColor = (s: number | null | undefined) => {
    if (s == null) return "text-muted-foreground";
    if (s > 0) return "text-emerald-500";
    if (s < 0) return "text-red-400";
    return "text-muted-foreground";
  };

  return (
    <td className="px-2 py-2 text-center">
      <div className="flex justify-center gap-1 items-center">
        {/* Data column */}
        {isManual && editing ? (
          <Input
            ref={inputRef}
            type="number"
            step="any"
            value={localVal}
            onChange={(e) => setLocalVal(e.target.value)}
            onBlur={handleSave}
            onKeyDown={handleKeyDown}
            className="h-6 w-16 text-xs text-center px-1"
          />
        ) : (
          <span
            className={cn(
              "text-xs tabular-nums min-w-[40px]",
              isManual && "cursor-pointer border-b border-dashed border-muted-foreground/50 hover:border-primary px-1",
              !isManual && "text-foreground"
            )}
            onClick={handleStartEdit}
            title={isManual ? "Clique para editar" : undefined}
          >
            {fmt(rawValue)}
          </span>
        )}
        {/* KPI score */}
        <span className={cn("text-xs tabular-nums font-medium min-w-[32px]", kpiColor(kpiScore))}>
          {kpiFmt(kpiScore)}
        </span>
      </div>
    </td>
  );
}

const TIPO_LABELS: Record<string, string> = {
  proporcional: "Prop.",
  escalonado_percentual: "Esc. %",
  escalonado_nps: "Esc. NPS",
  penalidade_percentual: "Pen. %",
  penalidade: "Penal.",
  binaria: "Binária",
  sim_nao_assiduidade: "Sim/Não",
  penalidade_taxa: "Pen. Tx",
};
