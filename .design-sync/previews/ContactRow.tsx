import { ContactRow } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, maxWidth: 480 };

export function WithHref() {
  return (
    <div style={wrapperStyle}>
      <ContactRow label="Email" value="aditf.work@gmail.com" href="mailto:aditf.work@gmail.com" />
    </div>
  );
}

export function WithoutHref() {
  return (
    <div style={wrapperStyle}>
      <ContactRow label="Location" value="Surakarta, Central Java, Indonesia" />
    </div>
  );
}
