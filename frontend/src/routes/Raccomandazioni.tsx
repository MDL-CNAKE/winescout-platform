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
    <section>
      <h2>Motore di Raccomandazione Content-Based</h2>
      <p className="hint">Trova vini chimicamente simili utilizzando la Similarità Coseno.</p>

      <label>
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
        <button disabled={!selectedId} onClick={() => setMode("similar")}>
          🎯 Trova Vini Simili
        </button>
        <button disabled={!selectedId} onClick={() => setMode("cheaper")}>
          💶 Trova Alternativa Più Economica
        </button>
      </div>

      {mode === "similar" && similarQuery.data && (
        <>
          <h3>Top 5 vini simili al vino ID {selectedId}</h3>
          <table>
            <thead>
              <tr><th>Nome</th><th>Tipo</th><th>Alcol</th><th>Qualità</th><th>Prezzo</th><th>Similarità</th></tr>
            </thead>
            <tbody>
              {similarQuery.data.map((r) => (
                <tr key={r.id}>
                  <td>{r.name}</td><td>{r.type}</td><td>{r.alcohol.toFixed(1)}%</td>
                  <td>{r.quality}</td><td>{r.price_eur.toFixed(2)} EUR</td>
                  <td>{(r.similarity * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {mode === "cheaper" && cheaperQuery.data && (
        <>
          <h3>Alternative più economiche al vino ID {selectedId}</h3>
          {cheaperQuery.data.length === 0 ? (
            <p>Nessuna alternativa più economica trovata tra i vini chimicamente simili.</p>
          ) : (
            <>
              <table>
                <thead>
                  <tr><th>Nome</th><th>Prezzo</th><th>Similarità</th><th>Risparmio</th></tr>
                </thead>
                <tbody>
                  {cheaperQuery.data.map((r) => (
                    <tr key={r.id}>
                      <td>{r.name}</td><td>{r.price_eur.toFixed(2)} EUR</td>
                      <td>{(r.similarity * 100).toFixed(1)}%</td>
                      <td>{(r.savings_pct * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="caption">
                Ordinato per un punteggio combinato: 70% similarità chimica, 30%
                risparmio economico — privilegia la coerenza del profilo
                gustativo rispetto al solo prezzo più basso.
              </p>
            </>
          )}
        </>
      )}
    </section>
  );
}
