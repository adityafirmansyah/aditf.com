export interface Stat {
  num: string;
  label: string;
}

export interface StatRowProps {
  stats: Stat[];
}

export function StatChip({ num, label }: Stat) {
  return (
    <div className="stat-chip">
      <span className="stat-chip__num">{num}</span>
      <span className="stat-chip__label">{label}</span>
    </div>
  );
}

export function StatRow({ stats }: StatRowProps) {
  return (
    <div className="stat-row">
      {stats.map((stat) => (
        <StatChip key={stat.label} {...stat} />
      ))}
    </div>
  );
}
