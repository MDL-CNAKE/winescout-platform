/**
 * Card di un singolo vino: bottiglia stilizzata + nome + statistiche +
 * descrizione breve generata dai dati reali (non testo inventato).
 */
import { BottleIcon } from "./BottleIcon";
import type { Wine } from "../api";

function alcoholDescriptor(alcohol: number): string {
  if (alcohol >= 12.0) return "corposo";
  if (alcohol <= 9.5) return "leggero";
  return "equilibrato";
}

function sugarDescriptor(sugar: number): string {
  if (sugar >= 10.0) return "dolce";
  if (sugar <= 2.0) return "secco";
  return "amabile";
}

function shortDescription(w: Wine): string {
  const body = alcoholDescriptor(w.alcohol);
  const sweetness = sugarDescriptor(w.residual_sugar);
  const pairing = w.food_pairing ? w.food_pairing.split(",")[0].split("(")[0].trim() : null;
  const base = `Un ${w.type === "red" ? "rosso" : "bianco"} ${body} e ${sweetness}, ${w.alcohol.toFixed(1)}% vol.`;
  return pairing ? `${base} Ideale con: ${pairing}.` : base;
}

interface WineCardProps {
  wine: Wine;
  selected: boolean;
  onSelect: (id: number) => void;
}

export function WineCard({ wine, selected, onSelect }: WineCardProps) {
  return (
    <div
      className={`wine-card${selected ? " selected" : ""}`}
      onClick={() => onSelect(wine.id)}
    >
      <BottleIcon type={wine.type} />
      <h4>{wine.name}</h4>
      <p className="wine-card-desc">{shortDescription(wine)}</p>
      <div className="wine-card-stats">
        <span>★ {wine.quality}/10</span>
        <span>{wine.price_eur?.toFixed(2) ?? "-"} EUR</span>
      </div>
    </div>
  );
}
