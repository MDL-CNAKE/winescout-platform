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
import { EmptyState } from "../components/EmptyState";

/** Hash deterministico dell'id, usato come chiave di ordinamento sparso. */
function shuffleKey(id: number): number {
  const x = Math.sin(id * 12.9898) * 43758.5453;
  return x - Math.floor(x);
}

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
    const matching = wines.filter(
      (w) =>
        (typeFilter === "Tutti" || w.type === typeFilter) &&
        w.quality >= minQuality
    );

    // Il CSV UCI elenca prima tutti i rossi e poi tutti i bianchi, con
    // campioni raggruppati per lotti analitici simili: rispettarne l'ordine
    // significa mostrare decine di card quasi identiche di fila. Si ordina
    // per un hash dell'id: l'ordine risulta vario ma deterministico (le card
    // non saltano fra un render e l'altro) e resta sempre una permutazione
    // valida, senza duplicati ne' vini persi.
    // Vedi docs/model_limitations.md.
    return [...matching].sort((a, b) => shuffleKey(a.id) - shuffleKey(b.id));
  }, [wines, typeFilter, minQuality]);

  if (isLoading) {
    return (
      <section>
        <EmptyState title="Il sommelier sta preparando il catalogo..." loading />
      </section>
    );
  }
  if (error) {
    return (
      <section>
        <EmptyState
          title="Non riesco a raggiungere il catalogo."
          hint="Verifica che il servizio sia attivo e riprova."
        />
      </section>
    );
  }

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

      {filtered.length === 0 ? (
        <EmptyState
          title="Nessun vino con questi criteri."
          hint="Prova ad abbassare la qualità minima o a cambiare tipo."
        />
      ) : (
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
      )}
    </section>
  );
}
