/**
 * Verdetto di abbinamento in forma strutturata.
 *
 * Differenza sostanziale rispetto alla chat con SVEVA: qui il modello non
 * scrive un paragrafo ma compila uno schema, validato lato server con
 * Pydantic. Il vantaggio non e' estetico —
 *
 *  - il giudizio sta su una scala chiusa di quattro valori, quindi puo'
 *    essere reso con un colore e in futuro ordinato o filtrato;
 *  - il campo "dato citato" costringe il modello a esibire il numero su cui
 *    si sta basando: se quel campo e' vuoto o generico, l'ancoraggio ai dati
 *    dichiarato nel prompt non c'e' stato, e chi legge se ne accorge;
 *  - quando il giudizio e' negativo lo schema pretende un'alternativa, cosi'
 *    un "no" resta comunque utile a chi lavora in cantina.
 *
 * Il numero di tentativi viene mostrato apposta: se il modello ha dovuto
 * essere corretto, e' un'informazione onesta sul funzionamento del sistema,
 * non un dettaglio da nascondere.
 */
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { chiediVerdetto } from "../api";
import { MetricheRisposta } from "./MetricheRisposta";

const COLORE: Record<string, string> = {
  ottimo: "verdetto-ottimo",
  buono: "verdetto-buono",
  accettabile: "verdetto-accettabile",
  sconsigliato: "verdetto-sconsigliato",
};

export function VerdettoAbbinamentoScheda({ wineId }: { wineId: number }) {
  const [piatto, setPiatto] = useState("");

  const mutation = useMutation({
    mutationFn: () => chiediVerdetto(wineId, piatto.trim()),
  });

  const v = mutation.data?.verdetto;

  return (
    <div className="verdetto-blocco">
      <p className="hint">
        Descrivi un piatto: il modello risponde con un giudizio su scala fissa, la
        motivazione e il dato del lotto su cui si basa.
      </p>

      <div className="verdetto-form">
        <input
          type="text"
          value={piatto}
          placeholder="Es: tagliata di manzo al rosmarino"
          onChange={(e) => setPiatto(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && piatto.trim() && !mutation.isPending) mutation.mutate();
          }}
        />
        <button
          className="btn-primary"
          disabled={!piatto.trim() || mutation.isPending}
          onClick={() => mutation.mutate()}
        >
          {mutation.isPending ? "Valutazione..." : "Valuta abbinamento"}
        </button>
      </div>

      {mutation.isError && (
        <p className="error">
          Il modello non ha prodotto un verdetto conforme allo schema. Riprova, oppure
          usa il sommelier in forma libera.
        </p>
      )}

      {v && (
        <div className="result-card">
          <p className={`verdetto-esito ${COLORE[v.giudizio]}`}>{v.giudizio}</p>
          <p>{v.motivazione}</p>

          <p className="verdetto-dato">
            <span className="verdetto-dato-etichetta">Dato citato</span>
            {v.dato_citato}
          </p>

          {v.profilo_alternativo && (
            <p className="verdetto-alternativa">
              <span className="verdetto-dato-etichetta">Profilo piu' indicato</span>
              {v.profilo_alternativo}
            </p>
          )}

          {mutation.data!.tentativi > 1 && (
            <p className="caption">
              Il primo output non rispettava lo schema: il modello e' stato corretto e
              ha risposto una seconda volta.
            </p>
          )}

          <MetricheRisposta metriche={mutation.data!.metriche} />
        </div>
      )}
    </div>
  );
}
