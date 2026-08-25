import { LangChip } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, display: 'inline-flex' };

export function Indonesian() {
  return (
    <div style={wrapperStyle}>
      <LangChip name="Indonesian" level="Native" />
    </div>
  );
}

export function English() {
  return (
    <div style={wrapperStyle}>
      <LangChip name="English" level="Professional Working Proficiency" />
    </div>
  );
}
