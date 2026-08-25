import { Crate } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, maxWidth: 480 };

export function Frontend() {
  return (
    <div style={wrapperStyle}>
      <Crate label="Frontend" items={['React', 'Next.js', 'React Native']} />
    </div>
  );
}

export function Backend() {
  return (
    <div style={wrapperStyle}>
      <Crate label="Backend" items={['Node.js', 'NestJS', 'REST APIs', 'gRPC', 'Microservices']} />
    </div>
  );
}
