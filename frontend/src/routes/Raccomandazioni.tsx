/**
 * Pagina Raccomandazioni: motore content-based (similarità coseno), stessa
 * logica della pagina Streamlit ma con due query separate su richiesta
 * dell'utente (simili / alternativa più economica).
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchWines, fetchRecommendations, fetchCheaperAlternatives } from "../api";

export function Raccomandazioni() {
  const { data: wines } = useQuery({ queryKey: ["wines"], queryFn: fetchWines });
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mode, setMode] = useState<"similar" | "cheaper" | null>(null);

  const similarQuery = useQuery({
    queryKey: ["recommend", selectedId],
    queryFn: () => fetchRecommendations(selectedId as number),
    enabled: mode === "similar" && selectedId !== null,
  });
  const cheaperQuery = useQuery({
    queryKey: ["cheaper", selectedId],
    queryFn: () => fetchCheaperAlternatives(selectedId as number),
    enabled: mode === "cheaper" && selectedId !== null,
  });

  return (
    <section className="page page-raccomandazioni">
      <header className="page-header">
        <h2>Motore di Raccomandazione</h2>
        <p className="hint">Trova vini chimicamente simili utilizzando la Similarità Coseno.</p>
      </header>

      <div className="predizione-card">
        <label className="type-select">
          Vino di partenza
          <select
            value={selectedId ?? ""}
            onChange={(e) => setSelectedId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">Seleziona un vino...</option>
            {wines?.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name} (ID {w.id})
              </option>
            ))}
          </select>
        </label>

        <div className="button-row">
          <button className="btn-primary" disabled={!selectedId} onClick={() => setMode("similar")}>
            Trova Vini Simili
          </button>
          <button className="btn-secondary" disabled={!selectedId} onClick={() => setMode("cheaper")}>
            Trova Alternativa Più Economica
          </button>
        </div>
      </div>

      {mode === "similar" && similarQuery.data && (
        <div className="reco-results">
          <h3>Top 5 vini simili al vino ID {selectedId}</h3>
          <div className="reco-table-wrap">
            <table className="reco-table">
              <thead>
                <tr>
                  <th>Nome</th><th>Tipo</th><th>Alcol</th><th>Qualità</th><th>Prezzo</th><th>Similarità</th>
                </tr>
              </thead>
              <tbody>
                {similarQuery.data.map((r) => (
                  <tr key={r.id}>
                    <td>{r.name}</td>
                    <td>{r.type}</td>
                    <td>{r.alcohol.toFixed(1)}%</td>
                    <td>{r.quality}</td>
                    <td>{r.price_eur.toFixed(2)} €</td>
                    <td>
                      <span className="similarity-pill">{(r.similarity * 100).toFixed(1)}%</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {mode === "cheaper" && cheaperQuery.data && (
        <div className="reco-results">
          <h3>Alternative più economiche al vino ID {selectedId}</h3>
          {cheaperQuery.data.length === 0 ? (
            <p className="hint">Nessuna alternativa più economica trovata tra i vini chimicamente simili.</p>
          ) : (
            <>
              <div className="reco-table-wrap">
                <table className="reco-table">
                  <thead>
                    <tr><th>Nome</th><th>Prezzo</th><th>Similarità</th><th>Risparmio</th></tr>
                  </thead>
                  <tbody>
                    {cheaperQuery.data.map((r) => (
                      <tr key={r.id}>
                        <td>{r.name}</td>
                        <td>{r.price_eur.toFixed(2)} €</td>
                        <td><span className="similarity-pill">{(r.similarity * 100).toFixed(1)}%</span></td>
                        <td><span className="savings-pill">-{(r.savings_pct * 100).toFixed(1)}%</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="caption">
                Ordinato per un punteggio combinato: 70% similarità chimica, 30%
                risparmio economico — privilegia la coerenza del profilo
                gustativo rispetto al solo prezzo più basso.
              </p>
            </>
          )}
        </div>
      )}
    </section>
  );
}
