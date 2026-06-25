import * as React from "react";

export interface IconProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Material Symbols Outlined ligature name, e.g. "dashboard". */
  name: string;
  /** Pixel size; also drives optical sizing. Default 20. */
  size?: number;
  /** Fill axis 0–1. Default 0 (outlined). */
  fill?: 0 | 1;
  /** Weight axis 100–700. Default 400. */
  weight?: number;
  /** Grade axis. Default 0. */
  grade?: number;
}

export function Icon(props: IconProps): JSX.Element;
