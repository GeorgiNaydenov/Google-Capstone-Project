import * as React from "react";

/**
 * Text input field, system-styled. 1px outline, focus = primary border.
 * @startingPoint section="Forms" subtitle="Inputs, selects, checkboxes" viewport="700x220"
 */
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  size?: "sm" | "md";
  /** Leading Material Symbols icon name. */
  icon?: string;
  invalid?: boolean;
}

export function Input(props: InputProps): JSX.Element;
