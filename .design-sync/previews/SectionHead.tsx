import { SectionHead } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, maxWidth: 720 };

export function About() {
  return (
    <div style={wrapperStyle}>
      <SectionHead eyebrow="Manifest — Contents Declaration" title="About" />
    </div>
  );
}

export function Projects() {
  return (
    <div style={wrapperStyle}>
      <SectionHead eyebrow="Cargo Log — Personal Freight" title="Projects" />
    </div>
  );
}
