"use client";

import { useConversationMessages } from "@/hooks/useConversations";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";

type MsgSide = "client" | "agent" | "bot";

function classifyMessage(direction: string, agentName: string | null): MsgSide {
  if (direction === "received") return "client";
  if (direction === "sent" && !agentName) return "bot";
  return "agent";
}

const sideStyles: Record<MsgSide, { align: string; bubble: string; label: string }> = {
  client: {
    align: "justify-start",
    bubble: "bg-white/10 text-foreground rounded-bl-sm",
    label: "Cliente",
  },
  agent: {
    align: "justify-end",
    bubble: "bg-primary/80 text-primary-foreground shadow-lg rounded-br-sm",
    label: "Agente",
  },
  bot: {
    align: "justify-start",
    bubble: "bg-amber-500/15 text-amber-100 border-amber-500/20 rounded-bl-sm",
    label: "Bot",
  },
};

export function ConversationDetailClient({
  id,
}: {
  id: string;
}) {
  const { messages, total, loading, error } = useConversationMessages(id);

  return (
    <div className="space-y-4">
      <Link href="/conversations" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" />
        Voltar
      </Link>

      <h1 className="text-2xl font-bold">Conversa #{id}</h1>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : error ? (
        <p className="text-destructive">{error}</p>
      ) : (
        <Card variant="glass">
          <CardHeader>
            <CardTitle className="text-base">
              Mensagens ({total ?? 0})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {messages?.map((m) => {
                const side = classifyMessage(m.direction, m.agent_name);
                const style = sideStyles[side];
                return (
                  <div key={m.message_id} className={`flex ${style.align}`}>
                    <div className={cn("max-w-[70%] rounded-lg border border-white/10 px-4 py-2 backdrop-blur-sm", style.bubble)}>
                      <p className="text-sm whitespace-pre-wrap break-words">{m.content || "(sem conteúdo)"}</p>
                      <div className="mt-1 flex items-center gap-2 flex-wrap">
                        <span className="text-[10px] opacity-70">
                          {m.created_at ? new Date(m.created_at).toLocaleString("pt-BR") : ""}
                        </span>
                        {side === "bot" ? (
                          <Badge variant="secondary" className="text-[10px] px-1 py-0 bg-amber-500/20 text-amber-300 border-amber-500/30">
                            <Bot className="mr-0.5 h-2.5 w-2.5" />
                            Bot
                          </Badge>
                        ) : m.agent_name ? (
                          <Badge variant="secondary" className="text-[10px] px-1 py-0">
                            {m.agent_name}
                          </Badge>
                        ) : null}
                        <Badge variant="outline" className="text-[10px] px-1 py-0 opacity-60">
                          {style.label}
                        </Badge>
                      </div>
                    </div>
                  </div>
                );
              })}
              {messages?.length === 0 && (
                <p className="text-center text-muted-foreground">Sem mensagens</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
