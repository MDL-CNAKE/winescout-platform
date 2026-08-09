/**
 * Predizione su un lotto NON ancora a catalogo.
 *
 * Non duplica la scheda Predizione della pagina vino, e la differenza e'
 * sostanziale: li' i valori sono quelli di un lotto esistente, gia' compilati
 * e non modificabili; qui si inseriscono a mano.
 *
 * Il caso d'uso e' quello dell'enologo con un'analisi in mano e una vasca in
 * lavorazione: il vino non e' in catalogo perche' non e' ancora imbottigliato.
 * E' anche il modo per rispondere a "e se abbassassi l'acidita' volatile?"
 * senza toccare i dati di un lotto reale.
 */
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { predictQuality, type PredictionInput } from "../api";
import { ValidationNote } from "../components/ValidationNote";
import { ImportanzaVariabili } from "../components/ImportanzaVariabili";

const DEFAULTS: PredictionInput = {
  type: "red",
  fixed_acidity: 7.0,
  volatile_acidity: 0.5,
  citric_acid: 0.3,
  residual_sugar: 2.0,
  chlorides: 0.08,
  free_sulfur_dioxide: 15.0,
  total_sulfur_dioxide: 100.0,
  density: 0.997,
  ph: 3.3,
  sulphates: 0.6,
  alcohol: 10.0,
};

const FIELDS: { key: keyof PredictionInput; label: string; step: number; min: number; max: number }[] = [
  { key: "fixed_acidity", label: "Acidità Fissa", step: 0.1, min: 4, max: 16 },
  { key: "volatile_acidity", label: "Acidità Volatile", step: 0.01, min: 0.1, max: 1.6 },
  { key: "citric_acid", label: "Acido Citrico", step: 0.01, min: 0, max: 1 },
  { key: "residual_sugar", label: "Zucchero Residuo", step: 0.1, min: 0.5, max: 65 },
  { key: "chlorides", label: "Cloruri", step: 0.001, min: 0.01, max: 0.6 },
  { key: "free_sulfur_dioxide", label: "SO2 Libera", step: 1, min: 1, max: 289 },
  { key: "total_sulfur_dioxide", label: "SO2 Totale", step: 1, min: 6, max: 440 },
  { key: "density", label: "Densità", step: 0.0001, min: 0.98, max: 1.04 },
  { key: "ph", label: "pH", step: 0.01, min: 2.7, max: 4.0 },
  { key: "sulphates", label: "Solfati", step: 0.01, min: 0.3, max: 2.0 },
  { key: "alcohol", label: "Alcol %", step: 0.1, min: 8, max: 15 },
];

export function Predizione() {
  const [form, setForm] = useState<PredictionInput>(DEFAULTS);
  const mutation = useMutation({ mutationFn: predictQuality });

  return (
    <section className="page page-predizione">
      <header className="page-header">
        <h2>
          <svg
            className="page-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M3 17l5-6 4 4 5-7 4 5" />
            <path d="M3 21h18" />
          </svg>
          Predizione Punteggio Qualità
        </h2>
        <p className="hint">
          Per un lotto <strong>non ancora a catalogo</strong>: inserisci i valori
          dell'analisi e ottieni la stima del punteggio (0-10). Per un vino già in
          catalogo apri la sua scheda, dove i valori sono già compilati.
        </p>
      </header>

      <div className="predizione-card">
        <label className="type-select">
          Tipo di vino
          <select
            value={form.type}
            onChange={(e) => setForm({ ...form, type: e.target.value as "red" | "white" })}
          >
            <option value="red">Rosso</option>
            <option value="white">Bianco</option>
          </select>
        </label>

        <div className="form-grid">
          {FIELDS.map((f) => (
            <label key={f.key} className="form-field">
              <span>{f.label}</span>
              <input
                type="number"
                step={f.step}
                min={f.min}
                max={f.max}
                value={form[f.key] as number}
                onChange={(e) => setForm({ ...form, [f.key]: Number(e.target.value) })}
              />
            </label>
          ))}
        </div>

        <button
          className="btn-primary"
          onClick={() => mutation.mutate(form)}
          disabled={mutation.isPending}
        >
          {mutation.isPending ? "Calcolo in corso..." : "Predici Qualità"}
        </button>

        {mutation.isError && <p className="error">Errore nella predizione. Riprova.</p>}

        {mutation.isSuccess && (
          <div className="result-card result-card--score">
            <span className="result-badge">{mutation.data.quality}<small>/10</small></span>
            <div>
              <h3>Punteggio Qualità Stimato</h3>
              <p className="caption">
                Il punteggio reale può variare in base a fattori non chimici
                (annata, terroir, affinamento) assenti dal dataset.
              </p>
            </div>
          </div>
        )}

        <ValidationNote kind="predizione" />
      </div>

      <ImportanzaVariabili />
    </section>
  );
}
