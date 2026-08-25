import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Hero } from './Hero';
import { Button } from '../Button';

describe('Hero', () => {
  it('renders name, accent, role, route, lede, status, and actions', () => {
    render(
      <Hero
        trackingLabel="TRACKING NO."
        trackingValue="AF-2011–2026"
        status="IN TRANSIT"
        name="Aditya"
        nameAccent="Firmansyah"
        role="Senior Software Engineer — Full-Stack Developer"
        origin="SURAKARTA, ID"
        dest="WORLDWIDE"
        lede="Thirteen-plus years shipping web, backend, and mobile software."
        actions={<Button variant="stamp" href="/cv.pdf">Download CV</Button>}
      />
    );

    expect(screen.getByText('Aditya')).toBeInTheDocument();
    expect(screen.getByText('Firmansyah')).toBeInTheDocument();
    expect(screen.getByText('Senior Software Engineer — Full-Stack Developer')).toBeInTheDocument();
    expect(screen.getByText('SURAKARTA, ID')).toBeInTheDocument();
    expect(screen.getByText('WORLDWIDE')).toBeInTheDocument();
    expect(screen.getByText('Thirteen-plus years shipping web, backend, and mobile software.')).toBeInTheDocument();
    expect(screen.getByText('IN TRANSIT')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Download CV' })).toBeInTheDocument();
  });
});
