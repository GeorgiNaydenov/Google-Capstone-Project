import * as React from "react";

/**
 * Core work-surface container — white panel, 1px border, 8px radius, no shadow.
 * @startingPoint section="Layout" subtitle="Bordered work-surface panel" viewport="700x240"
 */
export interface PanelProps {
  title?: React.ReactNode;
  /** Material Symbols icon name for the header. */
  icon?: string;
  iconColor?: string;
  /** Trailing header actions (buttons, chips). */
  actions?: React.ReactNode;
  children?: React.ReactNode;
  bodyPadding?: string;
  style?: React.CSSProperties;
  bodyStyle?: React.CSSProperties;
}

export function Panel(props: PanelProps): JSX.Element;
