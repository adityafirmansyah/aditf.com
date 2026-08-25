import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LangChip } from './LangChip';

describe('LangChip', () => {
  it('renders the language name and level', () => {
    render(<LangChip name="English" level="Professional Working Proficiency" />);
    expect(screen.getByText('English')).toBeInTheDocument();
    expect(screen.getByText('Professional Working Proficiency')).toBeInTheDocument();
  });
});
