/**
 * Card di un singolo vino: foto reale della bottiglia (rossa o bianca,
 * a rotazione per le bianche finché non abbiamo uno scatto per lotto) +
 * numero di lotto sovraimpresso, estratto dal nome reale del vino +
 * statistiche + descrizione breve generata dai dati reali.
 */
import bottleRed from "../assets/bottles/bottle-red.jpg";
import bottleWhite1 from "../assets/bottles/bottle-white-1.jpg";
import bottleWhite2 from "../assets/bottles/bottle-white-2.jpg";
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
function bottlePhoto(w: Wine): string {
  if (w.type === "red") return bottleRed;
  return w.id % 2 === 0 ? bottleWhite1 : bottleWhite2;
}
function lotLabel(name: string): string | null {
  const match = name.match(/Lotto #(\d+)/);
  return match ? `Lotto #${match[1]}` : null;
}

interface WineCardProps {
  wine: Wine;
  selected: boolean;
  onSelect: (id: number) => void;
}
export function WineCard({ wine, selected, onSelect }: WineCardProps) {
  const lot = lotLabel(wine.name);
  return (
    <div
      className={`wine-card${selected ? " selected" : ""}`}
      onClick={() => onSelect(wine.id)}
    >
      <div className="wine-card-photo">
        <img src={bottlePhoto(wine)} alt={wine.name} />
        {lot && <span className="wine-card-lot">{lot}</span>}
      </div>
      <h4>{wine.name}</h4>
      <p className="wine-card-desc">{shortDescription(wine)}</p>
      <div className="wine-card-stats">
        <span>★ {wine.quality}/10</span>
        <span>{wine.price_eur?.toFixed(2) ?? "-"} EUR</span>
      </div>
    </div>
  );
}
