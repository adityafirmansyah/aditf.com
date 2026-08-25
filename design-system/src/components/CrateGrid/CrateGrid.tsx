export interface CrateGroup {
  label: string;
  items: string[];
}

export interface CrateGridProps {
  groups: CrateGroup[];
}

export function Crate({ label, items }: CrateGroup) {
  return (
    <div className="crate">
      <p className="crate__label">{label}</p>
      <div className="crate__items">
        {items.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
    </div>
  );
}

export function CrateGrid({ groups }: CrateGridProps) {
  return (
    <div className="crate-grid">
      {groups.map((group) => (
        <Crate key={group.label} {...group} />
      ))}
    </div>
  );
}
