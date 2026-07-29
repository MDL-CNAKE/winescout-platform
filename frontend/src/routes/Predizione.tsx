/**
 * Pagina Predizione: form con gli stessi 11 parametri chimici della
 * versione Streamlit, invia a POST /api/predict e mostra il punteggio.
 */
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { predictQuality, type PredictionInput } from "../api";

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
    <section>
      <h2>Predizione Punteggio Qualità</h2>
      <p className="hint">
        Inserisci le caratteristiche chimiche del vino per ottenere una stima
        del punteggio (0-10).
      </p>

      <label>
        Tipo
        <select
          value={form.type}
          onChange={(e) => setForm({ ...form, type: e.target.value as "red" | "white" })}
        >
          <option value="red">red</option>
          <option value="white">white</option>
        </select>
      </label>

      <div className="form-grid">
        {FIELDS.map((f) => (
          <label key={f.key}>
            {f.label}
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

      <button onClick={() => mutation.mutate(form)} disabled={mutation.isPending}>
        {mutation.isPending ? "Calcolo..." : "🔮 Predici Qualità"}
      </button>

      {mutation.isError && <p className="error">Errore nella predizione. Riprova.</p>}

      {mutation.isSuccess && (
        <div className="result-card">
          <h3>Punteggio Qualità Stimato: {mutation.data.quality} / 10</h3>
          <p className="caption">
            Nota: questo è un modello predittivo basato su dati storici. Il
            punteggio reale può variare.
          </p>
        </div>
      )}
    </section>
  );
}
