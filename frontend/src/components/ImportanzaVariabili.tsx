/**
 * Cosa guida la qualità secondo il modello.
 *
 * Risponde alla domanda strategica (su cosa conviene concentrarsi in
 * generale), mentre le leve nella scheda del vino rispondono a quella
 * operativa (cosa fare su questo lotto). Insieme rendono il modello
 * spiegabile, non solo predittivo.
 */
import { useQuery } from "@tanstack/react-query";
import { fetchImportanza } from "../api";

export function ImportanzaVariabili() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["importanza"],
    queryFn: fetchImportanza,
    // Il primo calcolo richiede qualche secondo; una volta ottenuto non
    // cambia finche' il modello resta lo stesso.
    staleTime: Infinity,
  });

  if (isLoading) return <p className="hint">Analisi delle variabili in corso...</p>;
  if (isError || !data) return <p className="error">Analisi non disponibile.</p>;

  const massimo = Math.max(...data.map((v) => v.importanza), 0.0001);

  return (
    <section className="importanza">
      <h3>Cosa guida la qualità</h3>
      <p className="hint">
        Quanto peggiora la previsione se si rende inutilizzabile una variabile alla volta.
        Se rompere un parametro non peggiora nulla, quel parametro non serviva.
      </p>

      <ul className="imp-list">
        {data.map((v) => {
          const trascurabile = v.importanza <= 0.005;
          return (
            <li key={v.campo} className={`imp-item${trascurabile ? " trascurabile" : ""}`}>
              <div className="imp-head">
                <span className="imp-nome">{v.etichetta}</span>
                <span className="imp-quota">{trascurabile ? "≈ 0%" : `${v.quota}%`}</span>
              </div>
              <div className="imp-barra-sfondo">
                <div
                  className="imp-barra"
                  style={{ width: `${Math.max(1, (v.importanza / massimo) * 100)}%` }}
                  aria-hidden="true"
                />
              </div>
              <p className="imp-testo">{v.significato}</p>
            </li>
          );
        })}
      </ul>

      <p className="validation-note">
        <strong>Come è calcolata.</strong> Importanza per permutazione: si mescolano a caso i
        valori di una variabile e si misura di quanto cala l'R². Non si usa
        l'importanza interna del RandomForest perché sovrastima le variabili con molti valori
        distinti — un difetto rilevante su misure di laboratorio come queste. Il calcolo avviene
        sul test set, cioè su dati mai visti dal modello: sui dati di addestramento direbbe cosa
        il modello ha usato, qui dice cosa <em>generalizza</em>.
      </p>
    </section>
  );
}
