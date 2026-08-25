import { Nav } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24 };

export function Default() {
  return (
    <div style={wrapperStyle}>
      <Nav
        mark="AF"
        links={[
          { label: 'About', href: '#about', index: '01' },
          { label: 'Skills', href: '#skills', index: '02' },
          { label: 'Projects', href: '#projects', index: '03' },
          { label: 'Experience', href: '#experience', index: '04' },
          { label: 'Certs', href: '#certifications', index: '05' },
          { label: 'Contact', href: '#contact', index: '06' },
        ]}
      />
    </div>
  );
}
