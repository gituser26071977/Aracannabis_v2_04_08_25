import React from 'react';
import { render, screen } from '@testing-library/react';
import CardShell from './CardShell';

describe('CardShell — 5 states', () => {
  it('renders loading skeleton', () => {
    render(<CardShell title="X" state="loading">{null}</CardShell>);
    expect(screen.getByRole('region', { name: 'X' })).toHaveAttribute('aria-busy', 'true');
  });
  it('renders empty message', () => {
    render(<CardShell title="X" state="empty" emptyMessage="vazio aqui">{null}</CardShell>);
    expect(screen.getByText('vazio aqui')).toBeInTheDocument();
  });
  it('renders error message', () => {
    render(<CardShell title="X" state="error" errorMessage="boom">{null}</CardShell>);
    expect(screen.getByText('boom')).toBeInTheDocument();
  });
  it('renders offline banner', () => {
    render(<CardShell title="X" state="offline">{null}</CardShell>);
    expect(screen.getByText(/sem conex/i)).toBeInTheDocument();
  });
  it('renders children on success', () => {
    render(<CardShell title="X" state="success"><span>conteúdo</span></CardShell>);
    expect(screen.getByText('conteúdo')).toBeInTheDocument();
  });
});
