"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function DashboardError({ error, reset }: ErrorPageProps) {
  return (
    <div className="flex min-h-[50vh] items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-destructive">Erro inesperado</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Ocorreu um erro ao carregar o dashboard.
            {error.digest && (
              <span className="block mt-1 font-mono text-xs">
                Código: {error.digest}
              </span>
            )}
          </p>
          <Button onClick={reset} variant="default">
            Tentar novamente
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
