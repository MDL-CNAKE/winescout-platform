/**
 * Card di un singolo vino.
 *
 * Il titolo mostra solo la denominazione derivata dai dati chimici; il lotto
 * vive nel badge sulla foto (non ripetuto due volte) e il pH affianca il
 * titolo per distinguere a colpo d'occhio referenze con la stessa
 * denominazione, che nel dataset sono frequenti.
 *
 * Le caratteristiche sono etichette sintetiche invece di una frase
 * discorsiva: piu' rapide da confrontare fra card affiancate.
 */
import { BottleIcon } from "./BottleIcon";
import type { Wine } from "../api";
import {
  wineTitle,
  wineLot,
  alcoholDescriptor,
  sugarDescriptor,
  mainPairing,
} from "../lib/wineLabel";

interface WineCardProps {
  wine: Wine;
  selected: boolean;
  onSelect: (id: number) => void;
}

export function WineCard({ wine, selected, onSelect }: WineCardProps) {
  const lot = wineLot(wine.name);
  const pairing = mainPairing(wine);

  return (
    <div
      className={`wine-card${selected ? " selected" : ""}`}
      onClick={() => onSelect(wine.id)}
    >
      <div className="wine-card-photo">
        <BottleIcon wine={wine} size={130} />
        {lot && <span className="wine-card-lot">{lot}</span>}
      </div>

      <h4>{wineTitle(wine.name)}</h4>
      <p className="wine-card-sub">pH {wine.ph.toFixed(2)}</p>

      <div className="wine-card-tags">
        <span className="wine-tag">{wine.alcohol.toFixed(1)}% vol</span>
        <span className="wine-tag">
          {sugarDescriptor(wine.residual_sugar, wine.fixed_acidity)}
        </span>
        <span className="wine-tag">{alcoholDescriptor(wine.alcohol)}</span>
      </div>

      {pairing && <p className="wine-card-pairing">{pairing}</p>}

      <div className="wine-card-stats">
        <span>★ {wine.quality}/10</span>
        <span>{wine.price_eur?.toFixed(2) ?? "-"} EUR</span>
      </div>
    </div>
  );
}
