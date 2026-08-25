export interface ContactRowData {
  label: string;
  value: string;
  href?: string;
}

export interface ContactGridProps {
  rows: ContactRowData[];
}

export function ContactRow({ label, value, href }: ContactRowData) {
  const content = (
    <>
      <span className="contact-row__label">{label}</span>
      <span className="contact-row__value">{value}</span>
    </>
  );
  if (href) {
    const external = href.startsWith('http');
    return (
      <a
        className="contact-row"
        href={href}
        target={external ? '_blank' : undefined}
        rel={external ? 'noopener noreferrer' : undefined}
      >
        {content}
      </a>
    );
  }
  return <div className="contact-row contact-row--static">{content}</div>;
}

export function ContactGrid({ rows }: ContactGridProps) {
  return (
    <div className="contact-grid">
      {rows.map((row) => (
        <ContactRow key={row.label} {...row} />
      ))}
    </div>
  );
}
