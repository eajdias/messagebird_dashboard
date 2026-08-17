"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { NPSBadge } from "@/components/ui/metric-badge";
import type { AgentRankingItem } from "@/types";

interface AgentRankingProps {
  agents: AgentRankingItem[];
}

export function AgentRanking({ agents }: AgentRankingProps) {
  return (
    <Card variant="glass">
      <CardHeader>
        <CardTitle className="text-base">Ranking de Agentes</CardTitle>
      </CardHeader>
      <CardContent>
        {agents.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sem dados disponíveis</p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">#</TableHead>
                  <TableHead>Agente</TableHead>
                  <TableHead className="text-right">Chats</TableHead>
                  <TableHead className="text-right">Msgs</TableHead>
                  <TableHead className="text-right">NPS</TableHead>
                  <TableHead className="text-right">ART (min)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {agents.slice(0, 10).map((a) => (
                  <TableRow key={a.agent_name}>
                    <TableCell className="font-medium">{a.rank}</TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{a.agent_name}</div>
                        <div className="text-xs text-muted-foreground">
                          {a.department || a.group}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">{a.total_chats}</TableCell>
                    <TableCell className="text-right">{a.total_messages}</TableCell>
                    <TableCell className="text-right">
                      <NPSBadge value={a.nps_score} />
                    </TableCell>
                    <TableCell className="text-right">
                      {a.art_avg_minutes != null && Number.isFinite(a.art_avg_minutes)
                        ? a.art_avg_minutes.toFixed(1)
                        : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
