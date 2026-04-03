import { describe, it, expect } from 'vitest';
import { formatCurrency } from '../formatCurrency';

describe('formatCurrency', () => {
  it('formats 0 cents as $0.00', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });

  it('formats 199 cents as $1.99', () => {
    expect(formatCurrency(199)).toBe('$1.99');
  });

  it('formats 10000 cents as $100.00', () => {
    expect(formatCurrency(10000)).toBe('$100.00');
  });

  it('handles negative values', () => {
    expect(formatCurrency(-500)).toBe('-$5.00');
  });

  it('handles large numbers', () => {
    expect(formatCurrency(99999999)).toBe('$999,999.99');
  });

  it('supports custom locale', () => {
    expect(formatCurrency(1999, 'de-DE', 'EUR')).toContain('19,99');
  });

  it('supports custom currency', () => {
    const result = formatCurrency(1000, 'en-US', 'EUR');
    expect(result).toContain('10.00');
  });
});
