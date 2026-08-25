import { Button } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, display: 'inline-flex' };

export function Stamp() {
  return (
    <div style={wrapperStyle}>
      <Button variant="stamp" href="assets/Aditya_Firmansyah_CV.pdf" download>
        Download CV
      </Button>
    </div>
  );
}

export function Ghost() {
  return (
    <div style={wrapperStyle}>
      <Button variant="ghost" href="#contact">
        Get in touch
      </Button>
    </div>
  );
}
