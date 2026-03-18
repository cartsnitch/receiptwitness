const storeColors: Record<string, string> = {
  meijer: 'bg-meijer-red',
  kroger: 'bg-kroger-blue',
  target: 'bg-target-red',
}

const storeLetters: Record<string, string> = {
  meijer: 'M',
  kroger: 'K',
  target: 'T',
}

export function StoreIcon({ storeId, size = 'md' }: { storeId: string; size?: 'sm' | 'md' }) {
  const sizeClass = size === 'sm' ? 'h-6 w-6 text-xs' : 'h-8 w-8 text-sm'
  const bg = storeColors[storeId] ?? 'bg-gray-400'
  const letter = storeLetters[storeId] ?? storeId.charAt(0).toUpperCase()

  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-full font-bold text-white ${bg} ${sizeClass}`}
    >
      {letter}
    </span>
  )
}
