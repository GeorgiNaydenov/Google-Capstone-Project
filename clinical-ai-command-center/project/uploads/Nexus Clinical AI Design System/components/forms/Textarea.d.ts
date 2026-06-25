import * as React from "react";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  rows?: number;
  invalid?: boolean;
}

export function Textarea(props: TextareaProps): JSX.Element;
