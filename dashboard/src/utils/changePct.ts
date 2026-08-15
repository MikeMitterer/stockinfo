/**
 * Prozentuale Veränderung von `from` auf `to`.
 *
 * @returns Prozentwert, oder ``null`` bei `from === 0` bzw. ungültigen Zahlen.
 */
export function relChangePct(from: number, to: number): number | null {
  if (!Number.isFinite(from) || from === 0 || !Number.isFinite(to)) return null
  return ((to - from) / from) * 100
}

/**
 * Veränderung über die gesamte Serie (erster → letzter Punkt).
 *
 * @returns Prozentwert, oder ``null`` bei weniger als zwei Punkten.
 */
export function periodChangePct(series: { y: number }[]): number | null {
  if (series.length < 2) return null
  return relChangePct(series[0].y, series[series.length - 1].y)
}

/**
 * Grenzen für eine an die Kursachse gekoppelte Prozent-Achse.
 *
 * Liefert gepolsterte Kurs-Grenzen (`yMin`/`yMax`) und die dazu passenden
 * Prozent-Grenzen relativ zum ersten Punkt, sodass beide Achsen exakt dieselbe
 * physische Spanne abbilden (deckungsgleiche Nulllinie).
 *
 * @param series - Kursserie.
 * @param padRatio - Polsterung als Anteil der Kursspanne (Default 8 %).
 * @returns Grenzen, oder ``null`` bei < 2 Punkten bzw. erstem Wert 0/ungültig.
 */
export function pctAxisBounds(
  series: { y: number }[],
  padRatio = 0.08,
): { yMin: number; yMax: number; pctMin: number; pctMax: number } | null {
  if (series.length < 2) return null
  const first = series[0].y
  if (!Number.isFinite(first) || first === 0) return null
  const prices = series.map((point) => point.y)
  const lo = Math.min(...prices)
  const hi = Math.max(...prices)
  const pad = (hi - lo) * padRatio || Math.abs(hi) * 0.01 || 1
  const yMin = lo - pad
  const yMax = hi + pad
  return {
    yMin,
    yMax,
    pctMin: ((yMin - first) / first) * 100,
    pctMax: ((yMax - first) / first) * 100,
  }
}
