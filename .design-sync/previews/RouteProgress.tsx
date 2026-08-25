import { RouteProgress } from '@aditf/design-system';

// `transform` on this wrapper creates a new containing block, so RouteProgress's
// `position: fixed` bar renders relative to this box instead of escaping to the
// viewport (which is what it does correctly on the real page).
const wrapperStyle = {
  background: 'var(--ink)',
  padding: 24,
  maxWidth: 480,
  position: 'relative',
  height: 40,
  transform: 'translateZ(0)',
};

export function Default() {
  return (
    <div style={wrapperStyle}>
      <RouteProgress />
    </div>
  );
}
