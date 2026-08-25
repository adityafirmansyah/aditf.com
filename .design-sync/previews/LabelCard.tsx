import { LabelCard } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, maxWidth: 560 };

export function Bio() {
  return (
    <div style={wrapperStyle}>
      <LabelCard>
        Software engineer with 13+ years designing and building scalable web, backend, and mobile
        applications. Experienced across the full development lifecycle with React, Next.js,
        Node.js, NestJS, TypeScript, and WordPress.
      </LabelCard>
    </div>
  );
}
