export interface SectionHeadProps {
  eyebrow: string;
  title: string;
}

export function SectionHead({ eyebrow, title }: SectionHeadProps) {
  return (
    <div className="section__head">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
    </div>
  );
}
