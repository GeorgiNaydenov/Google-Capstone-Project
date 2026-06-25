import * as React from "react";

export interface EvidenceCitationProps {
  /** Superscript citation number. */
  index?: number;
  /** Source snippet text. */
  snippet?: React.ReactNode;
  sourceLabel?: string;
  onView?: () => void;
  style?: React.CSSProperties;
}

export function EvidenceCitation(props: EvidenceCitationProps): JSX.Element;
