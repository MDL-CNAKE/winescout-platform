/**
 * Vista Vendite: profili di mercato e redditività delle referenze.
 *
 * PERCHE' I PROFILI LI SCRIVE CHI VENDE
 * Il dataset non contiene geografia, clienti ne' storico vendite: nulla
 * permette di dedurre cosa piaccia in un certo mercato. La conoscenza
 * commerciale resta quindi umana — l'agente sa che il suo importatore cerca
 * bianchi secchi e agili — e viene dichiarata come profilo. Il sistema fa
 * cio' che sa fare: cercare fra 6497 lotti quelli che vi rispondono.
 *
 * PERCHE' DUE COLONNE DI MARGINE
 * Nella logica di pricing del progetto il margine percentuale e' inversamente
 * legato al prezzo: ordinare per percentuale metterebbe sempre in cima i vini
 * piu' economici. Il 63% su una bottiglia da 12 euro rende 7,56; il 42% su
 * una da 24 ne rende 10,08. Chi vende deve vedere entrambi i numeri, perche'
 * "spingi i margini migliori" e' un consiglio ambiguo finche' non si dice
 * quale dei due.
 */
import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchProfili,
  fetchViniPerProfilo,
  createProfilo,
  deleteProfilo,
  type MarketProfile,
} from "../api";
import { EmptyState } from "../components/EmptyState";
import { wineTitle, wineLot } from "../lib/wineLabel";

export function Vendite() {
  const queryClient = useQueryClient();
  const [attivo, setAttivo] = useState<number | null>(null);
  const [nuovo, setNuovo] = useState(false);

  const { data: profili } = useQuery({ queryKey: ["profili"], queryFn: fetchProfili });

  const { data: vini, isLoading: caricaVini } = useQuery({
    queryKey: ["profilo-vini", attivo],
    queryFn: () => fetchViniPerProfilo(attivo as number),
    enabled: attivo !== null,
  });

  const elimina = useMutation({
    mutationFn: deleteProfilo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profili"] });
      setAttivo(null);
    },
  });

  const profiloAttivo = profili?.find((p) => p.id === attivo) ?? null;

  return (
    <section>
      <header className="page-header">
        <h2>Profili di mercato</h2>
        <p className="hint">
          Descrivi cosa cerca un canale e trova le referenze che vi rispondono, ordinate per
          margine.
        </p>
      </header>

      <div className="profili-barra">
        <div className="filter-chips">
          {profili?.map((p) => (
            <button
              key={p.id}
              type="button"
              className={`filter-chip${attivo === p.id ? " active" : ""}`}
              onClick={() => setAttivo(attivo === p.id ? null : p.id)}
            >
              {p.name}
            </button>
          ))}
        </div>
        <button type="button" className="btn-secondary" onClick={() => setNuovo((v) => !v)}>
          {nuovo ? "Annulla" : "+ Nuovo profilo"}
        </button>
      </div>

      {nuovo && (
        <FormProfilo
          onFatto={(p) => {
            setNuovo(false);
            setAttivo(p.id);
          }}
        />
      )}

      {profiloAttivo && (
        <>
          <div className="profilo-scheda">
            <div>
              <h3>{profiloAttivo.name}</h3>
              {profiloAttivo.notes && <p className="caption">{profiloAttivo.notes}</p>}
              <p className="profilo-criteri">{descriviCriteri(profiloAttivo)}</p>
            </div>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => elimina.mutate(profiloAttivo.id)}
            >
              Elimina
            </button>
          </div>

          {caricaVini && <EmptyState title="Ricerca delle referenze..." loading />}

          {vini && vini.length === 0 && (
            <EmptyState
              title="Nessuna referenza risponde a questo profilo."
              hint="I criteri sono troppo stretti: prova ad allargare un intervallo."
            />
          )}

          {vini && vini.length > 0 && (
            <>
              <p className="caption">{vini.length} referenze, ordinate per margine in euro</p>
              <div className="reco-table-wrap">
                <table className="reco-table">
                  <thead>
                    <tr>
                      <th>Referenza</th>
                      <th>Lotto</th>
                      <th>Qualità</th>
                      <th>Alcol</th>
                      <th>Prezzo</th>
                      <th>Margine %</th>
                      <th>Margine €</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vini.map((v) => (
                      <tr key={v.id}>
                        <td>
                          <Link to="/vino/$wineId" params={{ wineId: String(v.id) }}>
                            {wineTitle(v.name)}
                          </Link>
                        </td>
                        <td className="caption">{wineLot(v.name)}</td>
                        <td>{v.quality}/10</td>
                        <td>{v.alcohol.toFixed(1)}%</td>
                        <td>{v.price_eur?.toFixed(2)} €</td>
                        <td className="margine-pct">{v.margin_pct?.toFixed(1)}%</td>
                        <td className="margine-euro">{v.margine_euro?.toFixed(2)} €</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <p className="validation-note">
                <strong>Le due colonne di margine dicono cose diverse.</strong> La percentuale
                premia le referenze economiche ad alta rotazione, il valore in euro premia quelle
                di fascia alta. L'ordinamento qui è sul margine in euro, cioè su quanto entra in
                cassa per bottiglia venduta. Attenzione però: prezzo e margine di questo catalogo
                sono <em>simulati</em> con una logica di business dichiarata, non sono listini
                reali.
              </p>
            </>
          )}
        </>
      )}

      {!profiloAttivo && !nuovo && (
        <EmptyState
          title="Scegli un profilo per vedere le referenze."
          hint="Oppure creane uno nuovo descrivendo cosa cerca il canale."
        />
      )}
    </section>
  );
}

/** Riassume i vincoli del profilo in una riga leggibile. */
function descriviCriteri(p: MarketProfile): string {
  const parti: string[] = [];
  if (p.wine_type) parti.push(p.wine_type === "red" ? "rossi" : "bianchi");
  if (p.min_quality != null) parti.push(`qualità ≥ ${p.min_quality}`);
  if (p.min_alcohol != null) parti.push(`alcol ≥ ${p.min_alcohol}%`);
  if (p.max_alcohol != null) parti.push(`alcol ≤ ${p.max_alcohol}%`);
  if (p.max_sugar != null) parti.push(`zucchero ≤ ${p.max_sugar} g/L`);
  if (p.min_acidity != null) parti.push(`acidità ≥ ${p.min_acidity} g/L`);
  if (p.max_price != null) parti.push(`prezzo ≤ ${p.max_price} €`);
  return parti.length > 0 ? parti.join(" · ") : "nessun vincolo: tutto il catalogo";
}

/* ---------------------------------------------------------------- */

const CAMPI = [
  { key: "min_quality", label: "Qualità minima", step: 1 },
  { key: "min_alcohol", label: "Alcol minimo %", step: 0.1 },
  { key: "max_alcohol", label: "Alcol massimo %", step: 0.1 },
  { key: "max_sugar", label: "Zucchero max g/L", step: 0.5 },
  { key: "min_acidity", label: "Acidità minima g/L", step: 0.1 },
  { key: "max_price", label: "Prezzo massimo €", step: 0.5 },
] as const;

function FormProfilo({ onFatto }: { onFatto: (p: MarketProfile) => void }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const [wineType, setWineType] = useState<"red" | "white" | null>(null);
  const [valori, setValori] = useState<Record<string, string>>({});

  const crea = useMutation({
    mutationFn: () =>
      createProfilo({
        name: name.trim(),
        notes: notes.trim() || null,
        wine_type: wineType,
        // I campi lasciati vuoti restano nulli: nessun vincolo su quel
        // parametro, invece di un valore arbitrario.
        min_quality: num(valori.min_quality),
        min_alcohol: num(valori.min_alcohol),
        max_alcohol: num(valori.max_alcohol),
        max_sugar: num(valori.max_sugar),
        min_acidity: num(valori.min_acidity),
        max_price: num(valori.max_price),
      }),
    onSuccess: (p) => {
      queryClient.invalidateQueries({ queryKey: ["profili"] });
      onFatto(p);
    },
  });

  return (
    <div className="predizione-card">
      <label className="field-block">
        Nome del profilo
        <input
          type="text"
          value={name}
          maxLength={80}
          placeholder="Es: Nord Europa - bianchi freschi"
          onChange={(e) => setName(e.target.value)}
        />
      </label>

      <label className="field-block">
        Note
        <input
          type="text"
          value={notes}
          maxLength={300}
          placeholder="Cosa cerca questo canale, in una riga"
          onChange={(e) => setNotes(e.target.value)}
        />
      </label>

      <div className="filter-group">
        <span className="filter-group-title">Tipo</span>
        <div className="filter-chips">
          {([null, "red", "white"] as const).map((t) => (
            <button
              key={String(t)}
              type="button"
              className={`filter-chip${wineType === t ? " active" : ""}`}
              onClick={() => setWineType(t)}
            >
              {t === null ? "Indifferente" : t === "red" ? "Rossi" : "Bianchi"}
            </button>
          ))}
        </div>
      </div>

      <div className="form-grid">
        {CAMPI.map((c) => (
          <label key={c.key} className="form-field">
            <span>{c.label}</span>
            <input
              type="number"
              step={c.step}
              placeholder="—"
              value={valori[c.key] ?? ""}
              onChange={(e) => setValori({ ...valori, [c.key]: e.target.value })}
            />
          </label>
        ))}
      </div>

      <p className="caption">
        I campi lasciati vuoti non filtrano nulla: un profilo può essere generico o molto stretto.
      </p>

      <button
        type="button"
        className="btn-primary"
        disabled={!name.trim() || crea.isPending}
        onClick={() => crea.mutate()}
      >
        Salva profilo
      </button>

      {crea.isError && <p className="error">Nome già esistente o dati non validi.</p>}
    </div>
  );
}

function num(v: string | undefined): number | null {
  if (v === undefined || v.trim() === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}
