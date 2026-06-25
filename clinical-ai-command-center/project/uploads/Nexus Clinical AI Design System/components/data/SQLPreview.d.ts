import * as React from "react";

export interface SQLPreviewProps {
  /** Plain SQL text. */
  code?: string;
  /** Pre-highlighted HTML (overrides code). */
  html?: string;
  label?: string;
  onCopy?: () => void;
  style?: React.CSSProperties;
}

export function SQLPreview(props: SQLPreviewProps): JSX.Element;
