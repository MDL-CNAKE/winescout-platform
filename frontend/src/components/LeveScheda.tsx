/**
 * Leve di miglioramento su un lotto: dove conviene intervenire in cantina.
 *
 * Ogni riga risponde a tre domande in una: quale parametro toccare, di
 * quanto, e quanto rende. L'intervento pratico e' scritto accanto, perche'
 * "abbassare l'acidita' volatile" senza dire come si fa non e' un consiglio
 * utilizzabile da chi sta in cantina.
 */
import { useQuery } from "@tanstack/react-query";
import { fetchLeve } from "../api";

export function LeveScheda({ wineId }: { wineId: number }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["leve", wineId],
    queryFn: () => fetchLeve(wineId),
    retry: false,
  });

  if (isLoading) return <p>Simulazione degli interventi in corso...</p>;
  if (isError || !data) return <p className="error">Simulazione non disponibile.</p>;

  const massimo = data.leve.length > 0 ? data.leve[0].delta_qualita : 1;

  return (
    <>
      <p className="hint">
        Previsione attuale del modello: <strong>{data.previsione_attuale.toFixed(2)}</strong> su 10
        {" "}(qualità rilevata in catalogo: {data.qualita_reale}). Di seguito le correzioni che
        alzerebbero di più la stima, valutate una alla volta.
      </p>

      {data.leve.length === 0 ? (
        <div className="leve-vuoto">
          <p>
            Nessuna correzione a singolo parametro migliora la stima di questo lotto entro un
            intervento realistico.
          </p>
          <p className="caption">
            Non significa che il vino non sia migliorabile: significa che, secondo il modello,
            il margine non sta in una singola leva. Serve agire su più parametri insieme, oppure
            il profilo è già in equilibrio per la sua categoria.
          </p>
        </div>
      ) : (
        <ul className="leve-list">
          {data.leve.map((l) => (
            <li key={l.campo} className="leva">
              <div className="leva-head">
                <span className="leva-azione">
                  {l.direzione === "ridurre" ? "Ridurre" : "Aumentare"} {l.etichetta.toLowerCase()}
                </span>
                <span className="leva-delta">+{l.delta_qualita.toFixed(2)}</span>
              </div>

              <div className="leva-valori">
                {l.valore_attuale} → <strong>{l.valore_proposto}</strong>
                {l.unita && ` ${l.unita}`}
              </div>

              <div
                className="leva-barra"
                style={{ width: `${Math.max(6, (l.delta_qualita / massimo) * 100)}%` }}
                aria-hidden="true"
              />

              <p className="leva-intervento">{l.intervento}</p>
            </li>
          ))}
        </ul>
      )}

      <p className="validation-note">
        <strong>Come leggere queste stime.</strong> Sono simulazioni sul modello, non garanzie:
        ogni parametro viene mosso singolarmente tenendo fermi gli altri. In cantina non funziona
        così — le variabili chimiche sono legate fra loro, e correggerne una ne sposta altre —
        quindi il guadagno reale sarà tipicamente inferiore a quello indicato. Il modello ha
        R² 0,56 sul test set: coglie la tendenza, non è un oracolo. I passi proposti sono
        correzioni realizzabili in una lavorazione reale, non spostamenti statistici astratti.
      </p>
    </>
  );
}
