import * as React from "react";

/**
 * Primary action button for Nexus Clinical AI. Flat, 1px border, 6px radius.
 * @startingPoint section="Core" subtitle="Action buttons in all variants" viewport="700x160"
 */
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md";
  /** Leading Material Symbols icon name. */
  icon?: string;
  /** Trailing Material Symbols icon name. */
  iconRight?: string;
  fullWidth?: boolean;
}

export function Button(props: ButtonProps): JSX.Element;
