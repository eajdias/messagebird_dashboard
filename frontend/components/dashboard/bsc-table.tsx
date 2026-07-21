"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface BSCTableProps {
  header: string[];
  data_t1: (string | number | null)[][];
  data_t2: (string | number | null)[][];
}

export function BSCTable({ header, data_t1, data_t2 }: BSCTableProps) {
  const hasData = header.length > 0 && (data_t1.length > 0 || data_t2.length > 0);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">BSC - Balanced Scorecard</CardTitle>
          <div className="flex gap-2">
            <Badge variant="success">T1</Badge>
            <Badge variant="warning">T2</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <p className="text-sm text-muted-foreground">Sem dados disponíveis</p>
        ) : (
          <div className="space-y-4">
            {data_t1.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      {header.map((h, i) => (
                        <th key={i} className="px-3 py-2 text-left font-medium text-muted-foreground">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data_t1.map((row, ri) => (
                      <tr key={ri} className="border-b">
                        {row.map((cell, ci) => (
                          <td key={ci} className="px-3 py-2">
                            {cell ?? ""}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {data_t2.length > 0 && (
              <div className="overflow-x-auto">
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">T2</h4>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      {header.map((h, i) => (
                        <th key={i} className="px-3 py-2 text-left font-medium text-muted-foreground">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data_t2.map((row, ri) => (
                      <tr key={ri} className="border-b">
                        {row.map((cell, ci) => (
                          <td key={ci} className="px-3 py-2">
                            {cell ?? ""}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
