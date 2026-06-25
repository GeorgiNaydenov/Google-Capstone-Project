import * as React from "react";

export interface DataTableColumn {
  key: string;
  header: React.ReactNode;
  align?: "left" | "right" | "center";
  /** Render value in JetBrains Mono (IDs, numbers, dates). */
  mono?: boolean;
  width?: string | number;
  /** Custom cell renderer. */
  render?: (row: any) => React.ReactNode;
}

/**
 * Dense data table — sticky header, zebra striping, 36px rows.
 * @startingPoint section="Data" subtitle="Dense clinical data table" viewport="700x260"
 */
export interface DataTableProps {
  columns: DataTableColumn[];
  rows: any[];
  zebra?: boolean;
  onRowClick?: (row: any) => void;
  style?: React.CSSProperties;
}

export function DataTable(props: DataTableProps): JSX.Element;
