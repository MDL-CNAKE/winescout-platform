/**
 * Bottiglia stilizzata in SVG, non un'emoji o clipart generico.
 * Il colore cambia in base al tipo di vino (rosso/bianco), usando le
 * stesse variabili CSS della palette del sito (bordeaux/gold).
 */
export function BottleIcon({ type }: { type: string }) {
  const isRed = type === "red";
  const glass = isRed ? "#6d1b2f" : "#cddc8f";
  const liquid = isRed ? "#4a1220" : "#e8d98a";

  return (
    <svg viewBox="0 0 60 140" width="48" height="112" aria-hidden="true">
      <rect x="26" y="4" width="8" height="28" rx="2" fill={glass} />
      <rect x="27" y="0" width="6" height="8" fill="#c9a24b" />
      <path
        d="M20 32 L20 26 Q20 20 26 20 L34 20 Q40 20 40 26 L40 32
           Q48 42 48 60 L48 128 Q48 136 40 136 L20 136 Q12 136 12 128
           L12 60 Q12 42 20 32 Z"
        fill={glass}
      />
      <path
        d="M14 70 L46 70 L46 128 Q46 134 40 134 L20 134 Q14 134 14 128 Z"
        fill={liquid}
      />
      <rect x="17" y="40" width="4" height="80" rx="2" fill="rgba(255,255,255,0.25)" />
    </svg>
  );
}
