import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LabelCard } from './LabelCard';

describe('LabelCard', () => {
  it('renders children inside the kraft card', () => {
    render(<LabelCard>Bio text goes here.</LabelCard>);
    const text = screen.getByText('Bio text goes here.');
    expect(text.closest('.label-card')).not.toBeNull();
  });
});
