import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Waybill } from './Waybill';

describe('Waybill', () => {
  it('renders label and value', () => {
    render(<Waybill label="TRACKING NO." value="AF-2011–2026" />);
    expect(screen.getByText('TRACKING NO.')).toBeInTheDocument();
    expect(screen.getByText('AF-2011–2026')).toBeInTheDocument();
  });

  it('renders the status when provided', () => {
    render(<Waybill label="TRACKING NO." value="AF-2011–2026" status="IN TRANSIT" />);
    expect(screen.getByText('IN TRANSIT')).toBeInTheDocument();
  });

  it('omits the status block when not provided', () => {
    render(<Waybill label="TRACKING NO." value="AF-2011–2026" />);
    expect(screen.queryByText('IN TRANSIT')).not.toBeInTheDocument();
  });
});
