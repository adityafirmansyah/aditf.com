export interface SealProps {
  label: string;
  sublabel: string;
}

export function Seal({ label, sublabel }: SealProps) {
  return (
    <div className="seal">
      <span>{label}</span>
      <small>{sublabel}</small>
    </div>
  );
}
