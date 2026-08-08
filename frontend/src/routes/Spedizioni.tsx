/**
 * Spedizioni — sezione in arrivo.
 *
 * Segnaposto dichiarato, non una pagina vuota: chi apre la sezione capisce
 * che la funzione e' prevista e cosa conterra'. Il grappolo-razzo e' l'unica
 * concessione decorativa del progetto, ed e' voluta: una pagina "in arrivo"
 * puo' permettersi di essere simpatica dove il resto dell'applicazione deve
 * restare sobrio.
 */
export function Spedizioni() {
  return (
    <section className="spedizioni">
      <div className="razzo">
        <svg viewBox="0 0 120 190" width="150" height="238" role="img" aria-label="Grappolo d'uva a razzo">
          {/* scia */}
          <g className="razzo-fiamma">
            <path d="M60 156 C52 172 56 186 60 190 C64 186 68 172 60 156 Z" fill="#e7d3a3" opacity="0.85" />
            <path d="M60 158 C55 170 58 180 60 183 C62 180 65 170 60 158 Z" fill="#fff6e0" />
          </g>

          {/* pinne */}
          <path d="M34 132 L20 154 L40 148 Z" fill="#8a2b3a" />
          <path d="M86 132 L100 154 L80 148 Z" fill="#8a2b3a" />

          {/* foglia e viticcio */}
          <path
            d="M60 18 C46 6 30 10 26 22 C38 30 52 28 60 18 Z"
            fill="#5e7a48"
          />
          <path
            d="M60 20 C68 12 80 12 86 18"
            fill="none"
            stroke="#5e7a48"
            strokeWidth="3"
            strokeLinecap="round"
          />

          {/* acini: il grappolo si stringe verso il basso, come un razzo */}
          {[
            [60, 40], [44, 52], [76, 52],
            [34, 70], [60, 66], [86, 70],
            [44, 86], [76, 86],
            [34, 104], [60, 100], [86, 104],
            [46, 118], [74, 118],
            [60, 134],
          ].map(([cx, cy], i) => (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r="13"
              fill={i % 3 === 0 ? "#7d2233" : i % 3 === 1 ? "#6d1b2f" : "#5a1526"}
              stroke="rgba(255,255,255,0.14)"
              strokeWidth="1.5"
            />
          ))}
          {/* riflessi */}
          <circle cx="56" cy="36" r="3.5" fill="rgba(255,255,255,0.35)" />
          <circle cx="40" cy="66" r="3" fill="rgba(255,255,255,0.25)" />
        </svg>
      </div>

      <h2>Spedizioni</h2>
      <p className="spedizioni-claim">In arrivo</p>
      <p className="hint">
        Qui troverai la preparazione degli ordini: cosa esce, in quale formato, con quale
        confezionamento e verso quale canale.
      </p>
      <p className="caption">
        Nel frattempo la scheda di ogni vino riporta già formato bottiglia, tappo ed etichetta
        nella sezione Packaging, e la vista Conservazione indica quali lotti conviene far
        partire per primi.
      </p>
    </section>
  );
}
