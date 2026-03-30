import { describe, it, expect } from 'vitest';
import { getStore, getStoreName, STORE_SLUGS } from '../storeSlugs';

describe('storeSlugs', () => {
  describe('STORE_SLUGS constant', () => {
    it('contains meijer, kroger, and target', () => {
      expect(STORE_SLUGS).toHaveProperty('meijer');
      expect(STORE_SLUGS).toHaveProperty('kroger');
      expect(STORE_SLUGS).toHaveProperty('target');
    });
  });

  describe('getStore', () => {
    it('returns store data for known slug', () => {
      const store = getStore('meijer');
      expect(store).toEqual({
        name: 'Meijer',
        color: '#e31837',
        icon: '/icons/stores/meijer.svg',
      });
    });

    it('returns null for unknown slug', () => {
      expect(getStore('unknown-store')).toBeNull();
    });

    it('is case insensitive', () => {
      expect(getStore('KROGER')).toBeTruthy();
      expect(getStore('Target')).toBeTruthy();
    });
  });

  describe('getStoreName', () => {
    it('returns store name for known slug', () => {
      expect(getStoreName('kroger')).toBe('Kroger');
    });

    it('returns raw slug for unknown store', () => {
      expect(getStoreName('unknown-store')).toBe('unknown-store');
    });

    it('is case insensitive', () => {
      expect(getStoreName('TARGET')).toBe('Target');
    });
  });
});
