import React from 'react';
import { AlertCircle } from 'lucide-react';
import clsx from 'clsx';

export const Alert = ({ children, className }) => (
  <div className={clsx("flex items-start gap-2 p-4 rounded-md border-l-4", className)}>
    <AlertCircle className="text-red-500 w-5 h-5 mt-1 shrink-0" />
    <div>{children}</div>
  </div>
);

export const AlertDescription = ({ children, className }) => (
  <p className={clsx("text-sm text-red-800", className)}>
    {children}
  </p>
);
