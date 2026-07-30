/**
 * Pagina dedicata a un singolo vino.
 *
 * Struttura: a sinistra la lista degli altri vini (navigazione rapida) con
 * i pulsanti di ritorno; a destra la scheda del vino e quattro schede
 * contestuali (predizione, raccomandazioni, packaging, sommelier) che
 * lavorano tutte su QUESTO vino, senza doverlo riselezionare ogni volta.
 */
import { useMemo, useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  fetchWines,
  fetchRecommendations,
  fetchCheaperAlternatives,
  fetchPackaging,
  predictQuality,
  askSommelier,
  type Wine,
  type PredictionInput,
} from "../api";
import { ChemicalRadar } from "../components/ChemicalRadar";
import { ValidationNote } from "../components/ValidationNote";
import { EmptyState } from "../components/EmptyState";
import { wineTitle, wineLot, allPairings } from "../lib/wineLabel";
import { BottleIcon } from "../components/BottleIcon";

type Tab = "predizione" | "raccomandazioni" | "packaging" | "sommelier";

const TABS: { key: Tab; label: string }[] = [
  { key: "predizione", label: "Predizione" },
  { key: "raccomandazioni", label: "Raccomandazioni" },
  { key: "packaging", label: "Packaging" },
  { key: "sommelier", label: "Sommelier" },
];

export function Vino() {
  const { wineId } = useParams({ from: "/vino/$wineId" });
  const id = Number(wineId);
  const [tab, setTab] = useState<Tab>("predizione");

  const { data: wines, isLoading } = useQuery({ queryKey: ["wines"], queryFn: fetchWines });
  const wine = useMemo(() => wines?.find((w) => w.id === id) ?? null, [wines, id]);

  if (isLoading) {
    return (
      <section>
        <EmptyState title="Il sommelier sta recuperando la scheda..." loading />
      </section>
    );
  }
  if (!wine) {
    return (
      <section>
        <EmptyState
          title="Questo vino non è in catalogo."
          hint="Torna al catalogo per sceglierne un altro."
        />
      </section>
    );
  }

  return (
    <section className="vino-layout">
      <aside className="vino-sidebar">
        <div className="vino-nav-buttons">
          <Link to="/catalogo" className="btn-secondary">← Torna al catalogo</Link>
        </div>
        <h4 className="vino-sidebar-title">Altri vini</h4>
        <ul className="vino-list">
          {wines
            ?.filter((w) => w.id !== id)
            .slice(0, 40)
            .map((w) => (
              <li key={w.id}>
                <Link to="/vino/$wineId" params={{ wineId: String(w.id) }}>
                  {wineTitle(w.name)} <em>{wineLot(w.name)}</em>
                </Link>
              </li>
            ))}
        </ul>
      </aside>

      <div className="vino-main">
        <div className="vino-hero">
          <div className="vino-photo">
            <BottleIcon wine={wine} size={230} />
          </div>
          <div className="vino-meta">
            <h2>{wineTitle(wine.name)}</h2>
            {wineLot(wine.name) && (
              <p className="vino-lot">Lotto {wineLot(wine.name)}</p>
            )}
            <p className="vino-stats">
              <span>{wine.type === "red" ? "Rosso" : "Bianco"}</span>
              <span>{wine.alcohol.toFixed(1)}% vol</span>
              <span>pH {wine.ph.toFixed(2)}</span>
              <span>Qualità {wine.quality}/10</span>
              <span>{wine.price_eur?.toFixed(2) ?? "-"} €</span>
            </p>
            {allPairings(wine).length > 0 && (
              <div className="vino-pairings">
                <p className="caption">Abbinamenti consigliati</p>
                <ul>
                  {allPairings(wine).map((dish) => (
                    <li key={dish}>{dish}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        <nav className="vino-tabs">
          {TABS.map((t) => (
            <button
              key={t.key}
              className={`vino-tab${tab === t.key ? " active" : ""}`}
              onClick={() => setTab(t.key)}
            >
              {t.label}
            </button>
          ))}
        </nav>

        <div className="vino-tab-panel">
          {tab === "predizione" && <TabPredizione wine={wine} />}
          {tab === "raccomandazioni" && <TabRaccomandazioni wineId={id} />}
          {tab === "packaging" && <TabPackaging wineId={id} />}
          {tab === "sommelier" && <TabSommelier wine={wine} />}
        </div>
      </div>
    </section>
  );
}

/* ---------------------------------------------------------------- */

/** I valori chimici assenti da /api/wines (citric acid, SO2, densità)
 *  restano modificabili: si parte da default plausibili per tipo. */
function TabPredizione({ wine }: { wine: Wine }) {
  const [form, setForm] = useState<PredictionInput>({
    type: wine.type,
    fixed_acidity: wine.fixed_acidity,
    volatile_acidity: wine.volatile_acidity,
    citric_acid: 0.3,
    residual_sugar: wine.residual_sugar,
    chlorides: wine.chlorides,
    free_sulfur_dioxide: wine.type === "red" ? 15 : 35,
    total_sulfur_dioxide: wine.type === "red" ? 46 : 138,
    density: 0.996,
    ph: wine.ph,
    sulphates: wine.sulphates,
    alcohol: wine.alcohol,
  });
  const mutation = useMutation({ mutationFn: predictQuality });

  const fields: { key: keyof PredictionInput; label: string; step: number }[] = [
    { key: "fixed_acidity", label: "Acidità Fissa", step: 0.1 },
    { key: "volatile_acidity", label: "Acidità Volatile", step: 0.01 },
    { key: "citric_acid", label: "Acido Citrico", step: 0.01 },
    { key: "residual_sugar", label: "Zucchero Residuo", step: 0.1 },
    { key: "chlorides", label: "Cloruri", step: 0.001 },
    { key: "free_sulfur_dioxide", label: "SO2 Libera", step: 1 },
    { key: "total_sulfur_dioxide", label: "SO2 Totale", step: 1 },
    { key: "density", label: "Densità", step: 0.0001 },
    { key: "ph", label: "pH", step: 0.01 },
    { key: "sulphates", label: "Solfati", step: 0.01 },
    { key: "alcohol", label: "Alcol %", step: 0.1 },
  ];

  return (
    <>
      <p className="hint">
        Parametri precompilati con il profilo di questo vino: modificali per simulare
        come cambierebbe il punteggio previsto dal modello.
      </p>

      <div className="form-grid">
        {fields.map((f) => (
          <label key={f.key} className="form-field">
            <span>{f.label}</span>
            <input
              type="number"
              step={f.step}
              value={form[f.key] as number}
              onChange={(e) => setForm({ ...form, [f.key]: Number(e.target.value) })}
            />
          </label>
        ))}
      </div>

      <button className="btn-primary" onClick={() => mutation.mutate(form)} disabled={mutation.isPending}>
        {mutation.isPending ? "Calcolo in corso..." : "Predici Qualità"}
      </button>

      {mutation.isError && <p className="error">Errore nella predizione. Riprova.</p>}

      {mutation.isSuccess && (
        <div className="result-card result-card--score">
          <span className="result-badge">{mutation.data.quality}<small>/10</small></span>
          <div>
            <h3>Punteggio previsto</h3>
            <p className="caption">
              Qualità reale in catalogo: {wine.quality}/10. Lo scarto dipende da fattori
              non chimici (annata, terroir, affinamento) che il modello non osserva.
            </p>
          </div>
        </div>
      )}

      <ChemicalRadar wine={wine} />
      <ValidationNote kind="predizione" />
    </>
  );
}

function TabRaccomandazioni({ wineId }: { wineId: number }) {
  const similar = useQuery({
    queryKey: ["recommend", wineId],
    queryFn: () => fetchRecommendations(wineId),
  });
  const cheaper = useQuery({
    queryKey: ["cheaper", wineId],
    queryFn: () => fetchCheaperAlternatives(wineId),
  });

  return (
    <>
      <h3>Vini simili</h3>
      {similar.isLoading && <p>Ricerca in corso...</p>}
      {similar.data && (
        <div className="reco-table-wrap">
          <table className="reco-table">
            <thead>
              <tr><th>Nome</th><th>Tipo</th><th>Alcol</th><th>Qualità</th><th>Prezzo</th><th>Similarità</th></tr>
            </thead>
            <tbody>
              {similar.data.map((r) => (
                <tr key={r.id}>
                  <td>
                    <Link to="/vino/$wineId" params={{ wineId: String(r.id) }}>{r.name}</Link>
                  </td>
                  <td>{r.type}</td>
                  <td>{r.alcohol.toFixed(1)}%</td>
                  <td>{r.quality}</td>
                  <td>{r.price_eur.toFixed(2)} €</td>
                  <td><span className="similarity-pill">{(r.similarity * 100).toFixed(1)}%</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h3>Alternative più economiche</h3>
      {cheaper.isLoading && <p>Ricerca in corso...</p>}
      {cheaper.data && cheaper.data.length === 0 && (
        <p className="hint">Nessuna alternativa più economica tra i vini chimicamente simili.</p>
      )}
      {cheaper.data && cheaper.data.length > 0 && (
        <>
          <div className="reco-table-wrap">
            <table className="reco-table">
              <thead>
                <tr><th>Nome</th><th>Prezzo</th><th>Similarità</th><th>Risparmio</th></tr>
              </thead>
              <tbody>
                {cheaper.data.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <Link to="/vino/$wineId" params={{ wineId: String(r.id) }}>{r.name}</Link>
                    </td>
                    <td>{r.price_eur.toFixed(2)} €</td>
                    <td><span className="similarity-pill">{(r.similarity * 100).toFixed(1)}%</span></td>
                    <td><span className="savings-pill">-{(r.savings_pct * 100).toFixed(1)}%</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="caption">
            Ordinato per un punteggio combinato: 70% similarità chimica, 30% risparmio,
            per privilegiare la coerenza del profilo gustativo sul solo prezzo.
          </p>
        </>
      )}

      <ValidationNote kind="raccomandazione" />
    </>
  );
}

function TabPackaging({ wineId }: { wineId: number }) {
  const { data, isLoading } = useQuery({ queryKey: ["packaging"], queryFn: fetchPackaging });
  const item = data?.find((p) => p.id === wineId);

  if (isLoading) return <p>Caricamento packaging...</p>;
  if (!item) return <p className="hint">Nessuna scheda packaging per questo vino.</p>;

  return (
    <dl className="packaging-specs">
      <div>
        <dt>Stile</dt>
        <dd><span className="packaging-style-badge">{item.style}</span></dd>
      </div>
      <div><dt>Formato bottiglia</dt><dd>{item.bottle_format}</dd></div>
      <div><dt>Tappo</dt><dd>{item.cap_type}</dd></div>
      <div><dt>Etichetta</dt><dd>{item.label_material}</dd></div>
    </dl>
  );
}

function TabSommelier({ wine }: { wine: Wine }) {
  const [question, setQuestion] = useState("");
  const mutation = useMutation({ mutationFn: () => askSommelier(question, wine.id) });

  return (
    <>
      <p className="hint">
        La risposta userà i dati reali di <strong>{wine.name}</strong> come contesto.
      </p>
      <textarea
        className="sommelier-input"
        placeholder="Es: 'Come lo presento a un cliente che ha ordinato pesce alla griglia?'"
        rows={4}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <button
        className="btn-primary"
        disabled={!question.trim() || mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? "Il sommelier sta pensando..." : "Chiedi al Sommelier"}
      </button>

      {mutation.isError && <p className="error">Errore nella chiamata al Sommelier.</p>}

      {mutation.isSuccess && (
        <div className="result-card">
          {mutation.data.demo_mode && (
            <p className="warning">Modalità demo: API key non configurata, risposta simulata.</p>
          )}
          <p>{mutation.data.answer}</p>
        </div>
      )}
    </>
  );
}
