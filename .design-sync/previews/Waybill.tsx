import { Waybill } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, display: 'inline-flex' };

export function WithStatus() {
  return (
    <div style={wrapperStyle}>
      <Waybill label="TRACKING NO." value="AF-2011–2026" status="IN TRANSIT" />
    </div>
  );
}

export function WithoutStatus() {
  return (
    <div style={wrapperStyle}>
      <Waybill label="TRACKING NO." value="AF-2011–2026" />
    </div>
  );
}
