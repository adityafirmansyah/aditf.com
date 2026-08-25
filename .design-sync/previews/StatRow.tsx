import { StatRow } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, maxWidth: 720 };

export function AboutStats() {
  return (
    <div style={wrapperStyle}>
      <StatRow
        stats={[
          { num: '13+', label: 'Years Shipping Code' },
          { num: '6', label: 'Portals & Apps Built at pickupp' },
          { num: '2', label: 'Languages — ID Native / EN Professional' },
        ]}
      />
    </div>
  );
}
