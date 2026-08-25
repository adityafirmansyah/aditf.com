import { Seal } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, display: 'inline-flex' };

export function JavaScriptCourse() {
  return (
    <div style={wrapperStyle}>
      <Seal label="JavaScript" sublabel="Course" />
    </div>
  );
}

export function CssFundamentals() {
  return (
    <div style={wrapperStyle}>
      <Seal label="CSS" sublabel="Fundamentals" />
    </div>
  );
}

export function JqueryCourse() {
  return (
    <div style={wrapperStyle}>
      <Seal label="jQuery" sublabel="Course" />
    </div>
  );
}
