"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { EvolutionMonth } from "@/types";

interface EvolutionChartProps {
  data: EvolutionMonth[];
}

export function EvolutionChart({ data }: EvolutionChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Evolução Mensal</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sem dados disponíveis</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="label" className="text-xs" />
              <YAxis className="text-xs" />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="total_conversations"
                name="Conversas"
                stroke="hsl(210, 100%, 50%)"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="nps_score"
                name="NPS"
                stroke="hsl(142, 76%, 36%)"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
