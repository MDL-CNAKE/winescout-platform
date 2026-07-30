/**
 * Galleria packaging: formato bottiglia, tappo ed etichetta derivati dal
 * profilo reale di ogni vino (qualità, prezzo, "Riserva" nel nome) via
 * endpoint backend /api/packaging. La bottiglia e' generata dai dati del
 * vino (BottleIcon), non e' una foto di repertorio: colore e capsula
 * riflettono tipo, gradazione e qualita' reali.
 */
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchPackaging } from "../api";
import { BottleIcon } from "../components/BottleIcon";

const STYLES = ["Tutti", "Moderno", "Classico", "Young", "Elegante"] as const;

export function Packaging() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["packaging"],
    queryFn: fetchPackaging,
  });
  const [styleFilter, setStyleFilter] = useState<(typeof STYLES)[number]>("Tutti");

  const filtered = useMemo(() => {
    if (!data) return [];
    return styleFilter === "Tutti" ? data : data.filter((p) => p.style === styleFilter);
  }, [data, styleFilter]);

  if (isLoading) return <p>Caricamento packaging...</p>;
  if (error) return <p className="error">Errore nel caricamento del packaging.</p>;

  return (
    <section>
      <div className="page-header">
        <h2>Packaging & Etichette</h2>
        <p className="hint">
          Formato bottiglia, tappo ed etichetta derivati dal profilo reale di ogni vino
          (qualità, prezzo, dicitura "Riserva").
        </p>
      </div>
      <div className="filters">
        <label>
          Stile
          <select value={styleFilter} onChange={(e) => setStyleFilter(e.target.value as typeof styleFilter)}>
            {STYLES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>
      </div>
      <p className="caption">
        {filtered.length} referenze nel filtro corrente.
      </p>
      <div className="packaging-grid">
        {filtered.map((p) => (
          <div key={p.id} className={`packaging-card style-${p.style.toLowerCase()}`}>
            <BottleIcon wine={p} size={130} />
            <h4>{p.name}</h4>
            <span className="packaging-style-badge">{p.style}</span>
            <p className="caption">{p.bottle_format}</p>
            <p className="caption">{p.cap_type}</p>
            <p className="caption">{p.label_material}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
