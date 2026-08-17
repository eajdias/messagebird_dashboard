import { Badge } from "@/components/ui/badge";

interface Thresholds {
  success: number;
  warning: number;
}

const NPS_THRESHOLDS: Thresholds = { success: 50, warning: 0 };
const RATING_THRESHOLDS: Thresholds = { success: 8, warning: 5 };
const ART_THRESHOLDS: Thresholds = { success: 10, warning: 30 };

function variantFromThresholds(
  value: number | null | undefined,
  t: Thresholds,
  invert: boolean = false,
): "success" | "warning" | "destructive" | "secondary" {
  if (value == null || !Number.isFinite(value)) return "secondary";
  if (invert) {
    if (value <= t.success) return "success";
    if (value <= t.warning) return "warning";
    return "destructive";
  }
  if (value >= t.success) return "success";
  if (value >= t.warning) return "warning";
  return "destructive";
}

export function NPSBadge({ value }: { value: number | null | undefined }) {
  return (
    <Badge variant={variantFromThresholds(value, NPS_THRESHOLDS)}>
      {value != null && Number.isFinite(value) ? value.toFixed(0) : "—"}
    </Badge>
  );
}

export function RatingBadge({ value }: { value: number | null | undefined }) {
  return (
    <Badge variant={variantFromThresholds(value, RATING_THRESHOLDS)}>
      {value != null && Number.isFinite(value) ? String(value) : "—"}
    </Badge>
  );
}

export function ArtBadge({ value }: { value: number | null | undefined }) {
  return (
    <Badge variant={variantFromThresholds(value, ART_THRESHOLDS, true)}>
      {value != null && Number.isFinite(value) ? `${value.toFixed(1)} min` : "—"}
    </Badge>
  );
}
