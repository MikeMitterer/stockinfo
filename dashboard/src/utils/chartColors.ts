/**
 * Baut Voll- und Flächenfarbe aus einem RGB-Tripel-Token („62 227 159").
 *
 * Seit der Token-Umstellung (T-11b) liefern die CSS-Custom-Properties keine
 * Hex-Literale mehr, sondern reine RGB-Tripel. Die alte Hex-Alpha-Verkettung
 * (`${hex}22`) funktioniert damit nicht mehr — `rgb(...)`-Strings lassen sich
 * nicht per String-Anhängsel verblassen. Stattdessen wird das Tripel direkt
 * in `rgb(r g b / a)`-Syntax eingesetzt.
 *
 * @param triplet - RGB-Tripel ohne Klammern, z.B. `"62 227 159"`.
 * @param alpha - Deckkraft der Flächenfarbe (Default 0.13 ≈ altes `22`-Hex-Alpha).
 * @returns Volle Farbe (`solid`) und teiltransparente Flächenfarbe (`fill`).
 */
export function accentColors(triplet: string, alpha = 0.13): { solid: string; fill: string } {
  return {
    solid: `rgb(${triplet})`,
    fill: `rgb(${triplet} / ${alpha})`,
  }
}
