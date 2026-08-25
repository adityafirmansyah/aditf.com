import type { ReactNode } from 'react';

export interface LabelCardProps {
  children: ReactNode;
}

export function LabelCard({ children }: LabelCardProps) {
  return (
    <div className="label-card">
      <span className="label-card__tape" aria-hidden="true" />
      <p>{children}</p>
    </div>
  );
}
