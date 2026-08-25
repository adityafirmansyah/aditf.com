import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Timeline } from './Timeline';

describe('Timeline', () => {
  it('renders one item per entry with role, org, date, status and bullets', () => {
    render(
      <Timeline
        items={[
          {
            date: 'Aug 2024 – Jul 2026',
            status: 'In Transit',
            statusVariant: 'transit',
            role: 'CTO',
            org: 'GOSG Consulting',
            bullets: ['Leads product and architecture.'],
            stack: ['AI Agents'],
          },
        ]}
      />
    );
    expect(screen.getByText('CTO')).toBeInTheDocument();
    expect(screen.getByText('— GOSG Consulting')).toBeInTheDocument();
    expect(screen.getByText('Aug 2024 – Jul 2026')).toBeInTheDocument();
    expect(screen.getByText('In Transit')).toHaveClass('timeline__badge--transit');
    expect(screen.getByText('Leads product and architecture.')).toBeInTheDocument();
    expect(screen.getByText('AI Agents')).toBeInTheDocument();
  });

  it('omits the stack row when no stack is given', () => {
    render(
      <Timeline
        items={[
          { date: '2018', status: 'Delivered', role: 'Developer', org: 'Studio', bullets: ['Shipped features.'] },
        ]}
      />
    );
    expect(screen.getByText('Delivered')).not.toHaveClass('timeline__badge--transit');
    expect(document.querySelector('.timeline__stack')).toBeNull();
  });
});
