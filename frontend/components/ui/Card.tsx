import type { ReactNode } from "react";

export function Card({
  title,
  right,
  children,
  className = "",
}: {
  title?: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border border-border bg-bg-card p-4 ${className}`}
    >
      {(title || right) && (
        <div className="mb-3 flex items-center justify-between">
          {title && (
            <h3 className="text-xs font-semibold uppercase tracking-widest text-txt-dim">
              {title}
            </h3>
          )}
          {right}
        </div>
      )}
      {children}
    </div>
  );
}
