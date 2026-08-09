/**
 * Vista di magazzino: il catalogo ordinato per rischio di conservazione,
 * con in cima i lotti da muovere per primi.
 *
 * Risponde alla domanda commerciale che una piccola cantina si pone davvero
 * — quali bottiglie posso tenere e quali devo far uscire adesso — che il
 * punteggio di qualita' da solo non risolve: i due valori sono quasi
 * scorrelati (0,16 sul catalogo), quindi un vino ottimo puo' essere mal
 * protetto e viceversa.
 */
import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { fetchConservazione } from "../api";
import { EmptyState } from "../components/EmptyState";
import { wineTitle, wineLot } from "../lib/wineLabel";

const TIPI = [
  { value: null, label: "Tutti" },
  { value: "red" as const, label: "Rossi" },
  { value: "white" as const, label: "Bianchi" },
];

export function Conservazione() {
  const [tipo, setTipo] = useState<"red" | "white" | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["conservazione-lista", tipo],
    queryFn: () => fetchConservazione(tipo, 60),
  });

  return (
    <section>
      <header className="page-header">
        <h2>Conservazione del magazzino</h2>
        <p className="hint">
          I lotti più esposti in cima: quelli da immettere sul mercato prima che
          il tempo lavori contro di loro. È una vista sull'<strong>intero
          magazzino</strong> — per gli indicatori di un singolo lotto apri la
          sua scheda.
        </p>
      </header>

      <div className="filters">
        <div className="filter-chips">
          {TIPI.map((t) => (
            <button
              key={String(t.value)}
              type="button"
              className={`filter-chip${tipo === t.value ? " active" : ""}`}
              onClick={() => setTipo(t.value)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading && <EmptyState title="Calcolo degli indicatori in corso..." loading />}
      {isError && (
        <EmptyState
          title="Non riesco a calcolare gli indicatori."
          hint="Verifica che il servizio sia attivo e riprova."
        />
      )}

      {data && (
        <>
          <div className="reco-table-wrap">
            <table className="reco-table cons-table">
              <thead>
                <tr>
                  <th>Referenza</th>
                  <th>Lotto</th>
                  <th>Qualità</th>
                  <th>Prezzo</th>
                  <th>Indice</th>
                  <th>Indicazione</th>
                </tr>
              </thead>
              <tbody>
                {data.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <Link to="/vino/$wineId" params={{ wineId: String(r.id) }}>
                        {wineTitle(r.name)}
                      </Link>
                    </td>
                    <td className="caption">{wineLot(r.name)}</td>
                    <td>{r.quality}/10</td>
                    <td>{r.price_eur != null ? `${r.price_eur.toFixed(2)} €` : "—"}</td>
                    <td>
                      <span className={`cons-pill livello-${level(r.punteggio)}`}>
                        {r.punteggio}
                      </span>
                    </td>
                    <td className="caption">{r.giudizio}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="validation-note">
            <strong>Su cosa si basa.</strong> Quattro parametri enologici:
            SO₂ molecolare (la frazione di solforosa realmente attiva, calcolata
            da SO₂ libera e pH), acidità volatile confrontata con i limiti di
            legge UE, pH e quota di solforosa ancora libera. È un sistema a
            regole, non un modello addestrato: il dataset non contiene
            informazioni sull'evoluzione dei vini nel tempo. Riguarda la
            stabilità chimica, non il potenziale di invecchiamento, che
            dipenderebbe da tannini e polifenoli qui assenti.
          </p>
        </>
      )}
    </section>
  );
}

function level(punteggio: number): string {
  if (punteggio >= 75) return "buono";
  if (punteggio >= 45) return "attenzione";
  return "critico";
}
