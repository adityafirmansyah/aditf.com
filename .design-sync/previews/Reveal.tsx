import { Reveal } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, maxWidth: 480 };

export function LedeParagraph() {
  return (
    <div style={wrapperStyle}>
      <Reveal>
        <p style={{ color: 'var(--paper-dim)', maxWidth: 480 }}>
          Software engineer with 13+ years designing and building scalable web, backend, and mobile applications.
        </p>
      </Reveal>
    </div>
  );
}
