import * as React from "react";

/**
 * Segmented control for switching clinical roles/views (e.g. Clinician/Admin).
 * @startingPoint section="Navigation" subtitle="Role switcher & tab bar" viewport="700x140"
 */
export interface RoleSwitcherProps {
  options: string[];
  value?: string;
  onChange?: (value: string) => void;
  style?: React.CSSProperties;
}

export function RoleSwitcher(props: RoleSwitcherProps): JSX.Element;
