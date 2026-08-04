/**
 * Barra sopra la griglia e pannello filtri a scomparsa.
 *
 * Il pannello e' un cassetto laterale con applicazione differita: le
 * modifiche vivono in una bozza locale e diventano effettive solo con
 * "Applica filtri". Con la ricerca lato server questo evita una richiesta
 * a ogni scatto di cursore, e lascia all'utente il tempo di comporre la
 * combinazione che vuole prima di vedere la griglia cambiare.
 */
import { useEffect, useState } from "react";
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

  return (
    <>
      <div className="filter-bar">
        <button
          type="button"
          className="filter-toggle"
          onClick={() => setOpen(true)}
          aria-haspopup="dialog"
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
        <FilterDrawer
          initial={filters}
          facets={facets}
          resultsPreview={total}
          onClose={() => setOpen(false)}
          onApply={(f) => {
            onFiltersChange(f);
            setOpen(false);
          }}
        />
      )}
    </>
  );
}

/* ---------------------------------------------------------------- */

interface FilterDrawerProps {
  initial: Filters;
  facets: WineFacets;
  resultsPreview: number | undefined;
  onClose: () => void;
  onApply: (f: Filters) => void;
}

function FilterDrawer({ initial, facets, onClose, onApply }: FilterDrawerProps) {
  const [draft, setDraft] = useState<Filters>(initial);

  // Chiusura con Esc e blocco dello scorrimento della pagina sotto: senza,
  // scorrendo dentro al cassetto si trascina anche la griglia.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previous;
    };
  }, [onClose]);

  const set = <K extends keyof Filters>(key: K, value: Filters[K]) =>
    setDraft((d) => ({ ...d, [key]: value }));

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
    const value = (draft[key] as number | null) ?? fallback;
    const untouched = draft[key] === null;
    return (
      <label className="filter-range" key={key}>
        <span>
          {label}
          <strong className={untouched ? "muted" : undefined}>
            {untouched ? "qualsiasi" : `${value.toFixed(step < 1 ? 1 : 0)}${unit}`}
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

  const chips = <T,>(
    title: string,
    key: keyof Filters,
    options: { value: T; label: string }[]
  ) => (
    <div className="filter-group">
      <span className="filter-group-title">{title}</span>
      <div className="filter-chips">
        {options.map((o) => (
          <button
            key={String(o.value)}
            type="button"
            className={`filter-chip${draft[key] === (o.value as never) ? " active" : ""}`}
            onClick={() => set(key, o.value as never)}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside
        className="filter-drawer"
        role="dialog"
        aria-modal="true"
        aria-label="Filtri del catalogo"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="drawer-head">
          <h2>Filtra</h2>
          <button
            type="button"
            className="drawer-clear"
            onClick={() => setDraft(EMPTY_FILTERS)}
            disabled={activeCount(draft) === 0}
          >
            Cancella i filtri
          </button>
          <button type="button" className="drawer-close" onClick={onClose} aria-label="Chiudi">
            ✕
          </button>
        </header>

        <div className="drawer-body">
          {chips("Categorie", "type", [
            { value: null, label: "Tutti" },
            { value: "red", label: "Rossi" },
            { value: "white", label: "Bianchi" },
          ])}

          {chips("Qualità minima", "min_quality", [
            { value: null, label: "Tutte" },
            { value: 5, label: "5+" },
            { value: 6, label: "6+" },
            { value: 7, label: "7+" },
            { value: 8, label: "8+" },
          ])}

          <div className="filter-group">
            <span className="filter-group-title">Profilo chimico</span>
            {range("Alcol minimo", "min_alcohol", facets.alcohol, 0.1, "%", "min")}
            {range("Zucchero residuo max", "max_sugar", facets.residual_sugar, 1, " g/L", "max")}
            {range("Acidità fissa minima", "min_acidity", facets.fixed_acidity, 0.1, " g/L", "min")}
          </div>

          <div className="filter-group">
            <span className="filter-group-title">Prezzo</span>
            {range("Prezzo massimo", "max_price", facets.price_eur, 1, " €", "max")}
          </div>
        </div>

        <footer className="drawer-foot">
          <button type="button" className="btn-primary drawer-apply" onClick={() => onApply(draft)}>
            Applica filtri
          </button>
        </footer>
      </aside>
    </div>
  );
}
