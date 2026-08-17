"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { NPSBadge } from "@/components/ui/metric-badge";
import type { ChannelItem } from "@/types";

interface ChannelBreakdownProps {
  channels: ChannelItem[];
}

export function ChannelBreakdown({ channels }: ChannelBreakdownProps) {
  if (channels.length === 0) {
    return (
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="text-base">Por Canal</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Sem dados disponíveis</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card variant="glass">
      <CardHeader>
        <CardTitle className="text-base">Por Canal</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {channels.map((c) => (
            <div
              key={c.channel_id}
              className="flex items-center justify-between rounded-lg border border-white/5 bg-white/5 p-3"
            >
              <div>
                <div className="text-sm font-medium">{c.channel_name}</div>
                <div className="text-xs text-muted-foreground">{c.total_messages} mensagens</div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary">{c.total_conversations}</Badge>
                {c.nps_score != null && Number.isFinite(c.nps_score) && (
                  <NPSBadge value={c.nps_score} />
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
