/**
 * Pagina Sommelier Virtuale.
 *
 * Due modalità, perché sono due problemi diversi e mescolarli peggiora
 * entrambi:
 *
 * - CONOSCENZA (RAG): domande sul sapere enologico. La risposta si fonda su
 *   passaggi recuperati dalla knowledge base indicizzata.
 * - CATALOGO (tool use): domande sui dati della cantina. Il modello non li
 *   conosce e non li può contenere nel prompt, quindi interroga il database
 *   attraverso strumenti con parametri tipizzati, e noi eseguiamo.
 *
 * La scelta è dell'utente e non automatica: indovinare l'intento sbagliando
 * significherebbe far rispondere a memoria una domanda sui dati, che è
 * esattamente il fallimento che questa separazione evita.
 */
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { fetchWines, askSommelier, chiediAgente } from "../api";
import { RobotSommelierIcon } from "../components/RobotSommelierIcon";
import { MetricheRisposta } from "../components/MetricheRisposta";
import { PassiAgente } from "../components/PassiAgente";

type Modalita = "conoscenza" | "catalogo";

export function Sommelier() {
  const { data: wines } = useQuery({ queryKey: ["wines"], queryFn: fetchWines });
  const [modalita, setModalita] = useState<Modalita>("conoscenza");
  const [useWine, setUseWine] = useState(false);
  const [wineId, setWineId] = useState<number | null>(null);
  const [question, setQuestion] = useState("");

  const rag = useMutation({
    mutationFn: () => askSommelier(question, useWine ? wineId : null),
  });
  const agente = useMutation({ mutationFn: () => chiediAgente(question) });

  const attiva = modalita === "conoscenza" ? rag : agente;

  const cambiaModalita = (m: Modalita) => {
    setModalita(m);
    // Le risposte non sono confrontabili fra le due modalità: lasciare a
    // schermo quella precedente farebbe credere che provenga dalla nuova.
    rag.reset();
    agente.reset();
  };

  return (
    <section>
      <div className="sommelier-header">
        <RobotSommelierIcon />
        <div>
          <h2>SVEVA</h2>
          <p className="sommelier-acronym">Sommelier Virtuale Esperta in Vini e Abbinamenti</p>
          <p className="sommelier-greeting">
            Ciao, sono SVEVA. Posso ragionare di abbinamenti, oppure andare a leggere
            cosa c'è davvero in catalogo.
          </p>
        </div>
      </div>

      <div className="modalita-switch" role="tablist">
        <button
          role="tab"
          aria-selected={modalita === "conoscenza"}
          className={`modalita-btn${modalita === "conoscenza" ? " active" : ""}`}
          onClick={() => cambiaModalita("conoscenza")}
        >
          Conoscenza enologica
        </button>
        <button
          role="tab"
          aria-selected={modalita === "catalogo"}
          className={`modalita-btn${modalita === "catalogo" ? " active" : ""}`}
          onClick={() => cambiaModalita("catalogo")}
        >
          Dati del catalogo
        </button>
      </div>

      <p className="hint">
        {modalita === "conoscenza"
          ? "Abbinamenti, note di degustazione, principi enologici. La risposta si basa sulla knowledge base."
          : "Quali lotti ho, a che prezzo, in che stato. SVEVA interroga il database: i numeri che cita vengono da lì."}
      </p>

      {modalita === "conoscenza" && (
        <>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={useWine}
              onChange={(e) => setUseWine(e.target.checked)}
            />
            <span>Basa la risposta su un vino del catalogo</span>
          </label>

          {useWine && (
            <label className="field-block">
              Vino di riferimento
              <select value={wineId ?? ""} onChange={(e) => setWineId(Number(e.target.value))}>
                <option value="">Seleziona...</option>
                {wines?.map((w) => (
                  <option key={w.id} value={w.id}>{w.name}</option>
                ))}
              </select>
            </label>
          )}
        </>
      )}

      <textarea
        className="sommelier-input"
        placeholder={
          modalita === "conoscenza"
            ? "Es: 'Come abbino un piatto molto grasso?'"
            : "Es: 'Quali rossi ho sopra qualità 6 sotto i 15 euro?'"
        }
        rows={4}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />

      <button
        className="btn-primary"
        disabled={!question.trim() || attiva.isPending}
        onClick={() => attiva.mutate()}
      >
        {attiva.isPending ? "SVEVA sta pensando..." : "Chiedi a SVEVA"}
      </button>

      {attiva.isError && <p className="error">Errore nella chiamata a SVEVA.</p>}

      {modalita === "conoscenza" && rag.isSuccess && (
        <div className="result-card">
          {rag.data.demo_mode && (
            <p className="warning">Modalità demo: API key non configurata, risposta simulata.</p>
          )}
          {rag.data.sources.length > 0 && (
            <details>
              <summary>Fonti consultate ({rag.data.sources.length} passaggi)</summary>
              {rag.data.sources.map((s, i) => (
                <p key={i} className="caption">{s.slice(0, 400)}...</p>
              ))}
            </details>
          )}
          <p>{rag.data.answer}</p>
          <MetricheRisposta metriche={rag.data.metriche} />
        </div>
      )}

      {modalita === "catalogo" && agente.isSuccess && (
        <div className="result-card">
          <p>{agente.data.answer}</p>
          <PassiAgente passi={agente.data.passi} />
          <MetricheRisposta metriche={agente.data.metriche} />
        </div>
      )}
    </section>
  );
}
