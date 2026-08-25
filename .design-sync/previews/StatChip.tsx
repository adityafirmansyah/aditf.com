import { StatChip } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, display: 'inline-flex' };

export function YearsShipping() {
  return (
    <div style={wrapperStyle}>
      <StatChip num="13+" label="Years Shipping Code" />
    </div>
  );
}

export function AppsBuilt() {
  return (
    <div style={wrapperStyle}>
      <StatChip num="6" label="Apps Built" />
    </div>
  );
}
