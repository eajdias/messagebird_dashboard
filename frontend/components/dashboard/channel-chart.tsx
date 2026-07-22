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

interface GroupedChannel {
  id: string;
  name: string;
  conversations: number;
  messages: number;
  percent: number;
}

function classifyChannel(name: string, id: string): "whatsapp" | "templates" | "outros" {
  const n = (name || id || "").toLowerCase();
  if (n.includes("whats")) return "whatsapp";
  if (n.includes("templat") || n.includes("template") || n.includes("site")) return "templates";
  return "outros";
}

function groupChannels(channels: ChannelItem[]): GroupedChannel[] {
  const buckets: Record<"whatsapp" | "templates" | "outros", GroupedChannel> = {
    whatsapp: { id: "whatsapp", name: "WhatsApp", conversations: 0, messages: 0, percent: 0 },
    templates: { id: "templates", name: "Templates", conversations: 0, messages: 0, percent: 0 },
    outros: { id: "outros", name: "Outros", conversations: 0, messages: 0, percent: 0 },
  };
  for (const c of channels) {
    const k = classifyChannel(c.channel_name, c.channel_id);
    buckets[k].conversations += c.total_conversations;
    buckets[k].messages += c.total_messages;
  }
  const total = Object.values(buckets).reduce((sum, b) => sum + b.conversations, 0);
  return Object.values(buckets)
    .map((b) => ({
      ...b,
      percent: total > 0 ? (b.conversations / total) * 100 : 0,
    }))
    .filter((b) => b.conversations > 0)
    .sort((a, b) => b.conversations - a.conversations);
}

interface TooltipPayloadEntry {
  name?: string;
  value?: number;
  payload?: GroupedChannel;
}

function safeNum(v: unknown, fallback = 0): number {
  if (typeof v === "number" && !Number.isNaN(v)) return v;
  if (typeof v === "string") {
    const n = Number(v);
    if (!Number.isNaN(n)) return n;
  }
  return fallback;
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
        {safeNum(data.conversations)} conversas ({safeNum(data.percent).toFixed(1)}%)
      </p>
      <p className="text-muted-foreground">{safeNum(data.messages)} mensagens</p>
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

  const data = groupChannels(channels);

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
                isAnimationActive={false}
              >
                {data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                content={<ChannelTooltip />}
                formatter={(value) => [safeNum(value), ""]}
              />
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
