/**
 * Barra sopra la griglia: filtri a sinistra, conteggio al centro,
 * ordinamento a destra.
 *
 * Il pannello dei filtri e' un blocco che si apre in linea invece di un
 * modale: su desktop resta visibile mentre la griglia si aggiorna sotto,
 * cosi' si vede subito l'effetto di ogni modifica.
 */
import { useState } from "react";
import type { SortOption, WineFacets } from "../api";

export interface Filters {
  type: "red" | "white" | null;
  min_quality: number | null;
  min_alcohol: number | null;
  max_alcohol: number | null;
  min_sugar: number | null;
  max_sugar: number | null;
  min_acidity: number | null;
  max_acidity: number | null;
  max_price: number | null;
}

export const EMPTY_FILTERS: Filters = {
  type: null,
  min_quality: null,
  min_alcohol: null,
  max_alcohol: null,
  min_sugar: null,
  max_sugar: null,
  min_acidity: null,
  max_acidity: null,
  max_price: null,
};

const SORT_LABELS: { value: SortOption; label: string }[] = [
  { value: "quality_desc", label: "Qualità decrescente" },
  { value: "quality_asc", label: "Qualità crescente" },
  { value: "price_asc", label: "Prezzo crescente" },
  { value: "price_desc", label: "Prezzo decrescente" },
  { value: "alcohol_desc", label: "Gradazione decrescente" },
  { value: "name_asc", label: "Nome (A-Z)" },
];

function activeCount(f: Filters): number {
  return Object.values(f).filter((v) => v !== null).length;
}

interface FilterBarProps {
  filters: Filters;
  onFiltersChange: (f: Filters) => void;
  sort: SortOption;
  onSortChange: (s: SortOption) => void;
  total: number | undefined;
  facets: WineFacets | undefined;
}

export function FilterBar({
  filters,
  onFiltersChange,
  sort,
  onSortChange,
  total,
  facets,
}: FilterBarProps) {
  const [open, setOpen] = useState(false);
  const active = activeCount(filters);

  const set = <K extends keyof Filters>(key: K, value: Filters[K]) =>
    onFiltersChange({ ...filters, [key]: value });

  /** Un cursore vale "nessun filtro" quando torna all'estremo del catalogo. */
  const range = (
    label: string,
    key: keyof Filters,
    [min, max]: [number, number],
    step: number,
    unit: string,
    mode: "min" | "max"
  ) => {
    const fallback = mode === "min" ? min : max;
    const value = (filters[key] as number | null) ?? fallback;
    return (
      <label className="filter-range">
        <span>
          {label}
          <strong>
            {value.toFixed(step < 1 ? 1 : 0)}
            {unit}
          </strong>
        </span>
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => {
            const n = Number(e.target.value);
            set(key, (mode === "min" ? n <= min : n >= max) ? null : n);
          }}
        />
      </label>
    );
  };

  return (
    <div className="filter-bar-wrap">
      <div className="filter-bar">
        <button
          type="button"
          className={`filter-toggle${open ? " open" : ""}`}
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
        >
          Filtra{active > 0 && <span className="filter-badge">{active}</span>}
        </button>

        <span className="filter-count">
          {total === undefined ? "…" : `${total.toLocaleString("it-IT")} risultati`}
        </span>

        <label className="filter-sort">
          Ordina per
          <select value={sort} onChange={(e) => onSortChange(e.target.value as SortOption)}>
            {SORT_LABELS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {open && facets && (
        <div className="filter-panel">
          <div className="filter-group">
            <span className="filter-group-title">Tipo</span>
            <div className="filter-chips">
              {([null, "red", "white"] as const).map((t) => (
                <button
                  key={String(t)}
                  type="button"
                  className={`filter-chip${filters.type === t ? " active" : ""}`}
                  onClick={() => set("type", t)}
                >
                  {t === null ? "Tutti" : t === "red" ? "Rossi" : "Bianchi"}
                </button>
              ))}
            </div>
          </div>

          <div className="filter-group">
            <span className="filter-group-title">Qualità minima</span>
            <div className="filter-chips">
              {[null, 5, 6, 7, 8].map((q) => (
                <button
                  key={String(q)}
                  type="button"
                  className={`filter-chip${filters.min_quality === q ? " active" : ""}`}
                  onClick={() => set("min_quality", q)}
                >
                  {q === null ? "Tutte" : `${q}+`}
                </button>
              ))}
            </div>
          </div>

          <div className="filter-group">
            <span className="filter-group-title">Profilo chimico</span>
            {range("Alcol minimo", "min_alcohol", facets.alcohol, 0.1, "%", "min")}
            {range("Zucchero residuo max", "max_sugar", facets.residual_sugar, 1, " g/L", "max")}
            {range("Acidità fissa minima", "min_acidity", facets.fixed_acidity, 0.1, " g/L", "min")}
            {range("Prezzo massimo", "max_price", facets.price_eur, 1, " €", "max")}
          </div>

          <button
            type="button"
            className="filter-reset"
            onClick={() => onFiltersChange(EMPTY_FILTERS)}
            disabled={active === 0}
          >
            Azzera filtri
          </button>
        </div>
      )}
    </div>
  );
}
