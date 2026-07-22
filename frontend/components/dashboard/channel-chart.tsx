"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { ChannelItem } from "@/types";

interface ChannelChartProps {
  channels: ChannelItem[];
  className?: string;
}

const COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

interface TooltipPayloadEntry {
  name?: string;
  value?: number;
  payload?: { name: string; conversations: number; messages: number; percent: number };
}

function ChannelTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayloadEntry[] }) {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  const data = item.payload;
  if (!data) return null;
  return (
    <div className="glass-tooltip rounded-lg px-3 py-2 text-xs">
      <p className="font-semibold">{data.name}</p>
      <p className="mt-1 text-muted-foreground">
        {data.conversations} conversas ({data.percent.toFixed(1)}%)
      </p>
      <p className="text-muted-foreground">{data.messages} mensagens</p>
    </div>
  );
}

export function ChannelChart({ channels, className }: ChannelChartProps) {
  if (channels.length === 0) {
    return (
      <Card variant="glass" className={className}>
        <CardHeader>
          <CardTitle className="text-base">Por Canal</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Sem dados disponíveis</p>
        </CardContent>
      </Card>
    );
  }

  const total = channels.reduce((sum, c) => sum + c.total_conversations, 0);
  const data = channels.map((c) => ({
    name: c.channel_name,
    conversations: c.total_conversations,
    messages: c.total_messages,
    percent: total > 0 ? (c.total_conversations / total) * 100 : 0,
  }));

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <CardTitle className="text-base">Por Canal</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[280px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={95}
                paddingAngle={2}
                dataKey="conversations"
                stroke="var(--background)"
                strokeWidth={2}
              >
                {data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<ChannelTooltip />} />
              <Legend
                verticalAlign="bottom"
                iconType="circle"
                wrapperStyle={{ fontSize: 12, paddingTop: 12 }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
