import React from 'react';
import clsx from 'clsx';

export const Card = ({ children, className }) => (
  <div className={clsx("bg-white rounded-xl shadow-md border border-gray-200", className)}>
    {children}
  </div>
);

export const CardHeader = ({ children, className }) => (
  <div className={clsx("px-6 pt-4 pb-2 border-b border-gray-100", className)}>
    {children}
  </div>
);

export const CardTitle = ({ children, className }) => (
  <h3 className={clsx("text-lg font-semibold text-gray-800", className)}>
    {children}
  </h3>
);

export const CardContent = ({ children, className }) => (
  <div className={clsx("px-6 py-4", className)}>
    {children}
  </div>
);
