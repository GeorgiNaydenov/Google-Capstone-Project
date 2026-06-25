import * as React from "react";

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Material Symbols icon name. */
  icon: string;
  size?: "sm" | "md";
  /** Accessible label / tooltip. */
  label?: string;
  /** Active/selected state (primary tonal fill). */
  active?: boolean;
}

export function IconButton(props: IconButtonProps): JSX.Element;
