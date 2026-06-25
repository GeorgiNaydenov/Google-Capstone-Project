import * as React from "react";

export interface TabsProps {
  tabs: string[];
  value?: string;
  onChange?: (tab: string) => void;
  style?: React.CSSProperties;
}

export function Tabs(props: TabsProps): JSX.Element;
