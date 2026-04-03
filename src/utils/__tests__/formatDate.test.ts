import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { formatDate } from '../formatDate';

describe('formatDate', () => {
  describe('short style', () => {
    it('formats an ISO date string', () => {
      const result = formatDate('2024-03-15', 'short');
      expect(result).toMatch(/Mar 15, 2024/);
    });

    it('formats a Date object', () => {
      const result = formatDate(new Date('2024-03-15'), 'short');
      expect(result).toMatch(/Mar 15, 2024/);
    });
  });

  describe('long style', () => {
    it('formats with weekday and full month name', () => {
      const result = formatDate('2024-03-15', 'long');
      expect(result).toMatch(/Friday/);
      expect(result).toMatch(/March/);
    });
  });

  describe('relative style', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('returns "just now" for very recent dates', () => {
      const now = new Date('2024-01-01T12:00:00Z');
      vi.setSystemTime(now);
      const result = formatDate(new Date('2024-01-01T11:59:59Z'), 'relative');
      expect(result).toBe('just now');
    });

    it('returns minutes ago', () => {
      const now = new Date('2024-01-01T12:00:00Z');
      vi.setSystemTime(now);
      const result = formatDate(new Date('2024-01-01T11:45:00Z'), 'relative');
      expect(result).toBe('15m ago');
    });

    it('returns hours ago', () => {
      const now = new Date('2024-01-01T12:00:00Z');
      vi.setSystemTime(now);
      const result = formatDate(new Date('2024-01-01T09:00:00Z'), 'relative');
      expect(result).toBe('3h ago');
    });

    it('returns days ago', () => {
      const now = new Date('2024-01-05T12:00:00Z');
      vi.setSystemTime(now);
      const result = formatDate(new Date('2024-01-01T12:00:00Z'), 'relative');
      expect(result).toBe('4d ago');
    });
  });
});
