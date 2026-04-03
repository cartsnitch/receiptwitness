export const STORE_SLUGS: Record<string, { name: string; color: string; icon: string }> = {
  meijer: { name: 'Meijer', color: '#e31837', icon: '/icons/stores/meijer.svg' },
  kroger: { name: 'Kroger', color: '#0033a0', icon: '/icons/stores/kroger.svg' },
  target: { name: 'Target', color: '#cc0000', icon: '/icons/stores/target.svg' },
};

export function getStore(slug: string) {
  return STORE_SLUGS[slug.toLowerCase()] ?? null;
}

export function getStoreName(slug: string): string {
  return getStore(slug)?.name ?? slug;
}
