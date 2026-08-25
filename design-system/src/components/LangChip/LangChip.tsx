export interface LangChipProps {
  name: string;
  level: string;
}

export function LangChip({ name, level }: LangChipProps) {
  return (
    <div className="lang-chip">
      <span className="lang-chip__name">{name}</span>
      <span className="lang-chip__level">{level}</span>
    </div>
  );
}
