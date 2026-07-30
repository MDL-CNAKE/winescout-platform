/**
 * Catalogo: griglia filtrabile di vini. Cliccando una card si apre la
 * pagina dedicata del vino (/vino/:id), dove vivono predizione,
 * raccomandazioni, packaging e sommelier per quel vino.
 */
import { useMemo, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { fetchWines } from "../api";
import { Carousel } from "../components/Carousel";
import { WineCard } from "../components/WineCard";

export function Catalogo() {
  const navigate = useNavigate();
  const { data: wines, isLoading, error } = useQuery({
    queryKey: ["wines"],
    queryFn: fetchWines,
  });

  const [typeFilter, setTypeFilter] = useState<"Tutti" | "red" | "white">("Tutti");
  const [minQuality, setMinQuality] = useState(0);

  const filtered = useMemo(() => {
    if (!wines) return [];
    return wines.filter(
      (w) =>
        (typeFilter === "Tutti" || w.type === typeFilter) &&
        w.quality >= minQuality
    );
  }, [wines, typeFilter, minQuality]);

  if (isLoading) return <p>Caricamento catalogo...</p>;
  if (error) return <p className="error">Errore nel caricamento del catalogo.</p>;

  return (
    <section>
      <h2>Catalogo Vini</h2>
      <p className="hint">Esplora il catalogo analizzato dai nostri modelli predittivi.</p>

      <div className="filters">
        <label>
          Tipo
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value as typeof typeFilter)}>
            <option value="Tutti">Tutti</option>
            <option value="red">Rossi</option>
            <option value="white">Bianchi</option>
          </select>
        </label>
        <label>
          Qualità minima
          <input
            type="number"
            min={0}
            max={10}
            value={minQuality}
            onChange={(e) => setMinQuality(Number(e.target.value))}
          />
        </label>
      </div>

      <p className="caption">{filtered.length} vini nel filtro corrente</p>

      <Carousel>
        {filtered.map((w) => (
          <WineCard
            key={w.id}
            wine={w}
            selected={false}
            onSelect={(id) => navigate({ to: "/vino/$wineId", params: { wineId: String(id) } })}
          />
        ))}
      </Carousel>
    </section>
  );
}
