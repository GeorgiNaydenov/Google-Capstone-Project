import * as React from "react";

/**
 * Compact status / risk indicator chip. Tonal bg, solid text, hairline border.
 * @startingPoint section="Feedback" subtitle="Status chips, confidence meter, citations" viewport="700x180"
 */
export interface StatusChipProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: "critical" | "warning" | "stable" | "verified" | "info" | "neutral";
  /** Optional leading Material Symbols icon. */
  icon?: string;
  children?: React.ReactNode;
}

export function StatusChip(props: StatusChipProps): JSX.Element;
