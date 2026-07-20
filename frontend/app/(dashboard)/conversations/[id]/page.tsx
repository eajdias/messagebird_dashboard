import { ConversationDetailClient } from "./conversation-detail-client";

export const dynamic = "force-dynamic";

export default async function ConversationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ConversationDetailClient id={id} />;
}
