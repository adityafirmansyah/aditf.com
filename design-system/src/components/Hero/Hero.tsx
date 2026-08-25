import type { ReactNode } from 'react';
import { Waybill } from '../Waybill';

export interface HeroProps {
  trackingLabel: string;
  trackingValue: string;
  status?: string;
  name: string;
  nameAccent: string;
  role: string;
  origin: string;
  dest: string;
  lede: string;
  actions: ReactNode;
}

export function Hero({
  trackingLabel,
  trackingValue,
  status,
  name,
  nameAccent,
  role,
  origin,
  dest,
  lede,
  actions,
}: HeroProps) {
  return (
    <section className="hero">
      <div className="hero__inner">
        <Waybill label={trackingLabel} value={trackingValue} status={status} />

        <h1 className="hero__name">
          <span>{name}</span>
          <span className="hero__name--accent">{nameAccent}</span>
        </h1>

        <p className="hero__role">{role}</p>

        <div className="route">
          <span className="route__origin">{origin}</span>
          <span className="route__line" aria-hidden="true" />
          <span className="route__dest">{dest}</span>
        </div>

        <p className="hero__lede">{lede}</p>

        <div className="hero__actions">{actions}</div>
      </div>
    </section>
  );
}
