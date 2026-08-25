import { ContactGrid } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, maxWidth: 720 };

export function Default() {
  return (
    <div style={wrapperStyle}>
      <ContactGrid
        rows={[
          { label: 'Email', value: 'aditf.work@gmail.com', href: 'mailto:aditf.work@gmail.com' },
          { label: 'Location', value: 'Surakarta, Central Java, Indonesia' },
          { label: 'GitHub', value: '/adityafirmansyah', href: 'https://github.com/adityafirmansyah' },
        ]}
      />
    </div>
  );
}
