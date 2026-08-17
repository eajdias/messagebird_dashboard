import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

interface SortIconProps {
  column: string;
  sortBy: string;
  sortOrder: "asc" | "desc";
}

export function SortIcon({ column, sortBy, sortOrder }: SortIconProps) {
  if (sortBy !== column) return <ArrowUpDown className="ml-1 h-3 w-3 opacity-40" />;
  return sortOrder === "asc" ? <ArrowUp className="ml-1 h-3 w-3" /> : <ArrowDown className="ml-1 h-3 w-3" />;
}
