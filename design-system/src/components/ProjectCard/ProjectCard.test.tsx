import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProjectCard } from './ProjectCard';

describe('ProjectCard', () => {
  it('renders title, subtitle, lede, points, stack and the live badge', () => {
    render(
      <ProjectCard
        eyebrow="Solo Build — Full-Stack Rust"
        title="GainForge"
        subtitle="Gamified Fitness RPG"
        badge={{ label: 'LIVE', href: 'https://gainforgeapp.com' }}
        lede="GainForge turns real workouts into RPG quests."
        points={['Full Rust stack front-to-back.', 'Designed the quest/XP/leveling system.']}
        stack={['Rust', 'Leptos (WASM)', 'Axum']}
        cta={{ label: 'Visit GainForge', href: 'https://gainforgeapp.com' }}
      />
    );

    expect(screen.getByText('GainForge')).toBeInTheDocument();
    expect(screen.getByText('Gamified Fitness RPG')).toBeInTheDocument();
    expect(screen.getByText('GainForge turns real workouts into RPG quests.')).toBeInTheDocument();
    expect(screen.getByText('Full Rust stack front-to-back.')).toBeInTheDocument();
    expect(screen.getByText('Rust')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /visit live site/i })).toHaveAttribute('href', 'https://gainforgeapp.com');
    expect(screen.getByRole('link', { name: /Visit GainForge/ })).toHaveAttribute('href', 'https://gainforgeapp.com');
  });

  it('omits the badge and CTA when not provided', () => {
    render(
      <ProjectCard
        eyebrow="Solo Build"
        title="Project"
        subtitle="Subtitle"
        lede="Lede text."
        points={['Point one.']}
        stack={['TypeScript']}
      />
    );
    expect(screen.queryByText('LIVE')).not.toBeInTheDocument();
  });
});
