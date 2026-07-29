import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchWines } from "../api";
import { Carousel } from "../components/Carousel";
import { WineCard } from "../components/WineCard";
import { ChemicalRadar } from "../components/ChemicalRadar";

export function Catalogo() {
  const { data: wines, isLoading, error } = useQuery({
    queryKey: ["wines"],
    queryFn: fetchWines,
  });

  const [typeFilter, setTypeFilter] = useState<"Tutti" | "red" | "white">("Tutti");
  const [minQuality, setMinQuality] = useState(0);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const filtered = useMemo(() => {
    if (!wines) return [];
    return wines.filter(
      (w) =>
        (typeFilter === "Tutti" || w.type === typeFilter) &&
        w.quality >= minQuality
    );
  }, [wines, typeFilter, minQuality]);

  const selected = filtered.find((w) => w.id === selectedId) ?? null;

  if (isLoading) return <p>Caricamento catalogo...</p>;
  if (error) return <p className="error">Errore nel caricamento del catalogo.</p>;

  return (
    <section>
      <h2>Catalogo Vini</h2>
      <p className="hint">Dati caricati dal database MySQL persistente via API.</p>

      <div className="filters">
        <label>
          Tipo
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value as typeof typeFilter)}>
            <option value="Tutti">Tutti</option>
            <option value="red">red</option>
            <option value="white">white</option>
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

      <p className="caption">
        Nota: prezzo e margine sono valori simulati con una logica di business
        (vedi src/pricing.py), non prezzi reali di listino. Descrizioni delle
        card generate dai dati chimici reali, non testo inventato.
      </p>

      <p className="caption">{filtered.length} vini nel filtro corrente</p>

      <Carousel>
        {filtered.map((w) => (
          <WineCard key={w.id} wine={w} selected={w.id === selectedId} onSelect={setSelectedId} />
        ))}
      </Carousel>

      {selected && (
        <div className="detail-card">
          <h3>{selected.name}</h3>
          <p>
            Prezzo: {selected.price_eur?.toFixed(2)} EUR · Qualità: {selected.quality}/10 ·
            Alcol: {selected.alcohol.toFixed(1)}%
          </p>
          <p>🍽️ <strong>Abbinamento consigliato:</strong> {selected.food_pairing}</p>
          <p className="caption">
            Abbinamento derivato dalle caratteristiche chimiche del vino secondo
            i principi enologici di contrapposizione e concordanza (vedi src/pairing.py).
          </p>
          <ChemicalRadar wine={selected} />
        </div>
      )}
    </section>
  );
}
