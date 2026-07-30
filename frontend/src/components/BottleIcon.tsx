/**
 * Bottiglia generata dai dati, non una foto di repertorio.
 *
 * Modellata su una bottiglia reale in vetro trasparente: il vino si vede per
 * tutta l'altezza, collo compreso, con un piccolo spazio d'aria sotto la
 * capsula. Tutto quello che cambia deriva dal profilo reale del vino,
 * coerentemente con il principio del progetto ("quello che leggi e' quello
 * che troverai nel bicchiere"):
 *
 *   - colore del vino: tonalita' dal tipo (paglierino/rubino), intensita'
 *     dalla gradazione alcolica, che nel dataset e' il proxy disponibile
 *     piu' vicino alla struttura del vino;
 *   - livello nel collo: zucchero residuo (i vini dolci appaiono piu'
 *     colmi, con meno spazio d'aria sotto la capsula);
 *   - capsula: oro per qualita' alta, stagnola scura altrimenti.
 *
 * Nessuna caratteristica inventata: se un dato non e' nel dataset (annata,
 * vitigno, denominazione reale) non compare nemmeno nel disegno, motivo per
 * cui l'etichetta e' una fascia muta e non riporta testo.
 */

/**
 * Il minimo necessario per disegnare la bottiglia: cosi' il componente e'
 * usabile anche dove non si dispone del profilo chimico completo (es. la
 * galleria packaging), che ricade su valori medi del dataset.
 */
export interface BottleData {
  id: number;
  type: string;
  quality: number;
  /** Il nome contiene "Riserva" per i vini che la logica di naming ha
   *  classificato come tali: da qui la veste piu' austera. */
  name?: string;
  alcohol?: number;
  residual_sugar?: number;
}

/** Medie del dataset, usate quando il dato puntuale non e' disponibile. */
const DEFAULT_ALCOHOL = 10.5;
const DEFAULT_SUGAR = 5.4;

/** Interpola fra due colori esadecimali (t da 0 a 1). */
function mix(a: string, b: string, t: number): string {
  const parse = (hex: string) => [
    parseInt(hex.slice(1, 3), 16),
    parseInt(hex.slice(3, 5), 16),
    parseInt(hex.slice(5, 7), 16),
  ];
  const [r1, g1, b1] = parse(a);
  const [r2, g2, b2] = parse(b);
  const k = Math.max(0, Math.min(1, t));
  const to2 = (n: number) => Math.round(n).toString(16).padStart(2, "0");
  return `#${to2(r1 + (r2 - r1) * k)}${to2(g1 + (g2 - g1) * k)}${to2(b1 + (b2 - b1) * k)}`;
}

interface Palette {
  wine: string;
  wineLight: string;
  wineDark: string;
  emptyGlass: string;
  cap: string;
  isRiserva: boolean;
}

function paletteFor(w: BottleData): Palette {
  const isRed = w.type === "red";
  const isRiserva = /riserva/i.test(w.name ?? "");
  // Gradazione normalizzata sul range del dataset (8-15% vol).
  const body = ((w.alcohol ?? DEFAULT_ALCOHOL) - 8) / 7;

  let wine = isRed
    ? mix("#a8394f", "#4a1220", body) // rubino chiaro -> granato profondo
    : mix("#f7f0cd", "#e0be63", body); // paglierino tenue -> dorato

  // Riserva: colore piu' concentrato, come un vino di lungo affinamento.
  if (isRiserva) wine = mix(wine, isRed ? "#2e0910" : "#b8863a", 0.35);

  return {
    wine,
    wineLight: mix(wine, "#ffffff", isRed ? 0.22 : 0.38),
    wineDark: mix(wine, "#000000", isRed ? 0.4 : 0.24),
    // Vetro vuoto sopra il livello del vino: trasparente per i bianchi,
    // appena piu' scuro per i rossi (bottiglie in vetro scuro).
    emptyGlass: isRed ? "#5b4038" : "#e9e6d4",
    // Riserva: capsula scura e austera invece dell'oro; l'oro resta alle
    // qualita' alte non Riserva.
    cap: isRiserva ? "#2a1017" : w.quality >= 7 ? "#c9a24b" : "#6b5a4a",
    isRiserva,
  };
}

export function BottleIcon({ wine, size = 112 }: { wine: BottleData; size?: number }) {
  const { wine: body, wineLight, wineDark, emptyGlass, cap, isRiserva } =
    paletteFor(wine);

  // Zucchero residuo -> spazio d'aria sotto la capsula: piu' dolce, piu'
  // colmo. Resta nel collo, come in una bottiglia reale.
  const sweetness = Math.max(
    0,
    Math.min(1, (wine.residual_sugar ?? DEFAULT_SUGAR) / 20)
  );
  const fillY = 60 - sweetness * 26;

  const gradId = `wine-${wine.id}`;
  const clipId = `bottle-${wine.id}`;

  // Profilo bordolese: collo lungo e stretto, spalla raccordata, corpo dritto.
  const shape =
    "M24 14 L24 56 C24 72 10 76 10 92 L10 168 Q10 176 18 176 " +
    "L42 176 Q50 176 50 168 L50 92 C50 76 36 72 36 56 L36 14 Z";

  return (
    <svg
      viewBox="0 0 60 180"
      width={size * 0.333}
      height={size}
      role="img"
      aria-label={`Bottiglia di vino ${wine.type === "red" ? "rosso" : "bianco"}`}
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={wineDark} />
          <stop offset="30%" stopColor={wineLight} />
          <stop offset="62%" stopColor={body} />
          <stop offset="100%" stopColor={wineDark} />
        </linearGradient>
        <clipPath id={clipId}>
          <path d={shape} />
        </clipPath>
      </defs>

      {/* Il vino riempie tutta la sagoma, collo compreso */}
      <path d={shape} fill={`url(#${gradId})`} />

      {/* Spazio d'aria sotto la capsula: vetro vuoto */}
      <rect
        x="8"
        y="0"
        width="44"
        height={fillY}
        fill={emptyGlass}
        clipPath={`url(#${clipId})`}
      />

      {/* Etichetta muta: nessun testo, perche' il dataset non contiene
          denominazioni reali */}
      <rect
        x="10"
        y="112"
        width="40"
        height="46"
        fill="rgba(247, 244, 232, 0.88)"
        clipPath={`url(#${clipId})`}
      />
      <rect
        x="10"
        y="146"
        width="40"
        height="4"
        fill="rgba(0, 0, 0, 0.07)"
        clipPath={`url(#${clipId})`}
      />

      {/* Riserva: filetto oro sull'etichetta, unico segno decorativo */}
      {isRiserva && (
        <>
          <rect
            x="10"
            y="117"
            width="40"
            height="1.2"
            fill="rgba(169, 132, 56, 0.85)"
            clipPath={`url(#${clipId})`}
          />
          <rect
            x="10"
            y="152"
            width="40"
            height="1.2"
            fill="rgba(169, 132, 56, 0.85)"
            clipPath={`url(#${clipId})`}
          />
        </>
      )}

      {/* Capsula sul collo: piu' lunga per le riserve */}
      <path
        d={isRiserva ? "M23 6 L37 6 L37 44 L23 44 Z" : "M23 6 L37 6 L37 32 L23 32 Z"}
        fill={cap}
        clipPath={`url(#${clipId})`}
      />
      <rect
        x="23"
        y={isRiserva ? 40 : 28}
        width="14"
        height="2.5"
        fill="rgba(0,0,0,0.28)"
      />

      {/* Riflessi sul vetro */}
      <rect x="15" y="66" width="3" height="42" rx="1.5" fill="rgba(255,255,255,0.3)" />
      <rect x="27.5" y="16" width="2" height="34" rx="1" fill="rgba(255,255,255,0.22)" />

      {/* Profilo del vetro */}
      <path d={shape} fill="none" stroke="rgba(0,0,0,0.28)" strokeWidth="1" />
    </svg>
  );
}
