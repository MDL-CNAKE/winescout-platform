/**
 * Pagina Sommelier Virtuale: chiama POST /api/sommelier, che dentro il
 * backend applica RAG + i guardrail sul prompt (niente vitigni inventati,
 * risposte brevi, onestà sull'abbinamento) già validati nella versione
 * Streamlit.
 */
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { fetchWines, askSommelier } from "../api";

export function Sommelier() {
  const { data: wines } = useQuery({ queryKey: ["wines"], queryFn: fetchWines });
  const [useWine, setUseWine] = useState(false);
  const [wineId, setWineId] = useState<number | null>(null);
  const [question, setQuestion] = useState("");

  const mutation = useMutation({
    mutationFn: () => askSommelier(question, useWine ? wineId : null),
  });

  return (
    <section>
      <h2>Sommelier Virtuale AI</h2>
      <p className="hint">Chiedi consigli su abbinamenti, note di degustazione o curiosità sul vino.</p>

      <label>
        <input type="checkbox" checked={useWine} onChange={(e) => setUseWine(e.target.checked)} />
        Basa la risposta su un vino del catalogo
      </label>

      {useWine && (
        <label>
          Vino di riferimento
          <select value={wineId ?? ""} onChange={(e) => setWineId(Number(e.target.value))}>
            <option value="">Seleziona...</option>
            {wines?.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        </label>
      )}

      <textarea
        placeholder="Es: 'Qual è l'abbinamento ideale per questo vino? Descrivilo a un cliente.'"
        rows={4}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />

      <button
        disabled={!question.trim() || mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? "Il sommelier sta pensando..." : "🤖 Chiedi al Sommelier"}
      </button>

      {mutation.isError && <p className="error">Errore nella chiamata al Sommelier.</p>}

      {mutation.isSuccess && (
        <div className="result-card">
          {mutation.data.demo_mode && (
            <p className="warning">⚠️ Modalità Demo: API Key non configurata. Risposta simulata.</p>
          )}
          {mutation.data.sources.length > 0 && (
            <details>
              <summary>📚 Fonti consultate ({mutation.data.sources.length} passaggi dalla knowledge base)</summary>
              {mutation.data.sources.map((s, i) => (
                <p key={i} className="caption">{s.slice(0, 400)}...</p>
              ))}
            </details>
          )}
          <p><strong>Risposta del Sommelier:</strong></p>
          <p>{mutation.data.answer}</p>
        </div>
      )}
    </section>
  );
}
