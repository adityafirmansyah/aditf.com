import { Barcode } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, maxWidth: 480 };

export function Default() {
  return (
    <div style={wrapperStyle}>
      <Barcode />
    </div>
  );
}
