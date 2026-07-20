"use client";

import { useConversationMessages } from "@/hooks/useConversations";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

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
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Mensagens ({total ?? 0})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {messages?.map((m) => (
                <div
                  key={m.message_id}
                  className={`flex ${m.direction === "outbound" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[70%] rounded-lg px-4 py-2 ${
                      m.direction === "outbound"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    }`}
                  >
                    <p className="text-sm">{m.content || "(sem conteúdo)"}</p>
                    <div className="mt-1 flex items-center gap-2">
                      <span className="text-[10px] opacity-70">
                        {m.created_at ? new Date(m.created_at).toLocaleString("pt-BR") : ""}
                      </span>
                      {m.agent_name && (
                        <Badge variant="secondary" className="text-[10px] px-1 py-0">
                          {m.agent_name}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
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
