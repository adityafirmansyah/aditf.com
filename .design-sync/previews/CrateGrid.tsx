import { CrateGrid } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24 };

export function Default() {
  return (
    <div style={wrapperStyle}>
      <CrateGrid
        groups={[
          { label: 'Languages', items: ['JavaScript (ES6+)', 'TypeScript', 'HTML5', 'CSS3'] },
          { label: 'Frontend', items: ['React', 'Next.js', 'React Native'] },
          { label: 'CMS', items: ['WordPress', 'Shopify'] },
          { label: 'Infrastructure', items: ['Kubernetes', 'Git', 'CI/CD'] },
          { label: 'Databases', items: ['MySQL', 'PostgreSQL'] },
        ]}
      />
    </div>
  );
}
