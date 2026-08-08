/**
 * Traccia delle chiamate agli strumenti fatte dal modello.
 *
 * Perche' mostrarla. Quando SVEVA dice "hai quattro rossi sotto i 12 euro",
 * chi legge non ha modo di distinguere un dato letto dal database da un
 * numero inventato: la frase e' identica nei due casi. Questi passi rendono
 * visibile la differenza — si vede quale strumento e' stato chiamato, con
 * quali filtri, e quante righe ha restituito.
 *
 * E' chiusa di default: chi si fida legge la risposta, chi vuole controllare
 * apre. L'informazione c'e' senza occupare la scena.
 */
import type { PassoAgente } from "../api";

const ETICHETTE: Record<string, string> = {
  cerca_vini: "Ricerca nel catalogo",
  scheda_lotto: "Scheda del lotto",
};

export function PassiAgente({ passi }: { passi: PassoAgente[] }) {
  if (passi.length === 0) {
    return (
      <p className="caption">
        Nessuno strumento consultato: la risposta non contiene dati del catalogo.
      </p>
    );
  }

  return (
    <details className="passi-agente">
      <summary>
        Dati consultati ({passi.length} {passi.length === 1 ? "chiamata" : "chiamate"})
      </summary>
      <ol className="passi-lista">
        {passi.map((p, i) => {
          const filtri = Object.entries(p.argomenti);
          return (
            <li key={i}>
              <span className="passo-nome">{ETICHETTE[p.strumento] ?? p.strumento}</span>
              {filtri.length > 0 && (
                <span className="passo-argomenti">
                  {filtri.map(([k, v]) => `${k}: ${String(v)}`).join(" · ")}
                </span>
              )}
              {p.risultati != null && (
                <span className="passo-esito">
                  {p.risultati === 0
                    ? "nessun lotto trovato"
                    : `${p.risultati} lotti`}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </details>
  );
}
