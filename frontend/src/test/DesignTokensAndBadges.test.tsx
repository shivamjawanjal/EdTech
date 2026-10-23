import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HealthBadge, Badge } from '../components/common/Badge';

describe('Design System Tokens and Pedagogical Badges', () => {
  it('renders On Track badge with emerald semantic styling', () => {
    render(<HealthBadge status="ON_TRACK" />);
    const badge = screen.getByText('On Track');
    expect(badge).toBeInTheDocument();
    expect(badge.closest('span')).toHaveClass('bg-emerald-50');
    expect(badge.closest('span')).toHaveClass('text-emerald-700');
  });

  it('renders Needs Attention badge with amber semantic styling', () => {
    render(<HealthBadge status="NEEDS_ATTENTION" />);
    const badge = screen.getByText('Needs Attention');
    expect(badge).toBeInTheDocument();
    expect(badge.closest('span')).toHaveClass('bg-amber-50');
    expect(badge.closest('span')).toHaveClass('text-amber-700');
  });

  it('renders At Risk badge with rose semantic styling', () => {
    render(<HealthBadge status="AT_RISK" />);
    const badge = screen.getByText('At Risk');
    expect(badge).toBeInTheDocument();
    expect(badge.closest('span')).toHaveClass('bg-rose-50');
    expect(badge.closest('span')).toHaveClass('text-rose-700');
  });

  it('renders general Badge variants', () => {
    render(<Badge variant="brand">Math Batch</Badge>);
    expect(screen.getByText('Math Batch')).toBeInTheDocument();
  });
});
