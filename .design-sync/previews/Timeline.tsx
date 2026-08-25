import { Timeline } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, maxWidth: 720 };

export function InTransitAndDelivered() {
  return (
    <div style={wrapperStyle}>
      <Timeline
        items={[
          {
            date: 'Aug 2024 – Jul 2026',
            status: 'In Transit',
            statusVariant: 'transit',
            role: 'CTO',
            org: 'GOSG Consulting',
            bullets: [
              'Leads product and architecture for a platform spanning website creation tools, an e-commerce system, and SEO tooling.',
              'Integrates AI agents into the platform to help users build sites, run their stores, and handle SEO with less manual effort.',
            ],
            stack: ['Website Builder', 'E-commerce', 'SEO Tools', 'AI Agents'],
          },
          {
            date: 'Apr 2019 – Jul 2024',
            status: 'Delivered',
            role: 'Software Engineer',
            org: 'pickupp, Singapore',
            bullets: [
              'Developed and maintained enterprise logistics platforms using React, Next.js, Node.js, and NestJS.',
              'Built scalable backend microservices in TypeScript communicating through gRPC.',
            ],
            stack: ['React', 'Next.js', 'Node.js', 'NestJS', 'TypeScript', 'Kubernetes', 'gRPC'],
          },
        ]}
      />
    </div>
  );
}
