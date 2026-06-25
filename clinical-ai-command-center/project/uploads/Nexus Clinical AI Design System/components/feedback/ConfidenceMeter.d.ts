import * as React from "react";

export interface ConfidenceMeterProps {
  /** 0–100. */
  value?: number;
  label?: string;
  /** Track width in px. Default 96. */
  width?: number;
  showValue?: boolean;
  /** Override the auto value-keyed color. */
  color?: string;
  style?: React.CSSProperties;
}

export function ConfidenceMeter(props: ConfidenceMeterProps): JSX.Element;
