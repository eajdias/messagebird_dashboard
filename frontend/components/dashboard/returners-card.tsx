"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ReturnersResponse } from "@/types";

interface ReturnersCardProps {
  data: ReturnersResponse | null;
  className?: string;
}

function safeNum(v: unknown, fallback = 0): number {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  return fallback;
}

const FREQ_COLORS = ["var(--chart-2)", "var(--chart-3)", "var(--chart-4)"] as const;

export function ReturnersCard({ data, className }: ReturnersCardProps) {
  const totalChats = safeNum(data?.total_chats);
  const totalUnique = safeNum(data?.total_unique);
  const totalReturners = safeNum(data?.total_returners);
  const pctReturning = data?.pct_returning ?? 0;

  const buckets = data?.buckets ?? [];
  const maxFreq = Math.max(...buckets.map((b) => b.count), 1);

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Retornantes</CardTitle>
          <span className="text-xs text-muted-foreground">{totalChats} chats</span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-2 flex items-baseline gap-2">
          <span className="text-3xl font-bold tabular-nums">{pctReturning.toFixed(1)}%</span>
          <span className="text-xs text-muted-foreground">
            {totalReturners} de {totalUnique} clientes retornaram
          </span>
        </div>

        {totalChats === 0 ? (
          <p className="text-xs text-muted-foreground">Sem dados de retorno no período</p>
        ) : (
          <>
            <p className="mb-3 text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
              Perfil dos {totalReturners} retornantes
            </p>
            <div className="space-y-1.5">
              {buckets.map((b, i) => (
                <div key={b.label} className="space-y-0.5">
                  <div className="flex items-center justify-between text-xs">
                    <span>{b.label}</span>
                    <span className="tabular-nums font-medium">
                      {b.count}{" "}
                      <span className="text-muted-foreground">({b.pct.toFixed(0)}%)</span>
                    </span>
                  </div>
                  <div className="h-2.5 overflow-hidden rounded-full bg-white/5">
                    <motion.div
                      className="h-full rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${(b.count / maxFreq) * 100}%` }}
                      transition={{ duration: 0.5, delay: 0.1 + i * 0.08, ease: "easeOut" }}
                      style={{ background: FREQ_COLORS[i] ?? FREQ_COLORS[2] }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
