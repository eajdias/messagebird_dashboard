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
import type { ChannelItem } from "@/types";

interface ChannelBreakdownProps {
  channels: ChannelItem[];
}

export function ChannelBreakdown({ channels }: ChannelBreakdownProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Por Canal</CardTitle>
      </CardHeader>
      <CardContent>
        {channels.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sem dados disponíveis</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Canal</TableHead>
                <TableHead className="text-right">Conversas</TableHead>
                <TableHead className="text-right">Msgs</TableHead>
                <TableHead className="text-right">NPS</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {channels.map((c) => (
                <TableRow key={c.channel_id}>
                  <TableCell className="font-medium">{c.channel_name}</TableCell>
                  <TableCell className="text-right">{c.total_conversations}</TableCell>
                  <TableCell className="text-right">{c.total_messages}</TableCell>
                  <TableCell className="text-right">
                    {c.nps_score != null ? c.nps_score.toFixed(1) : "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
