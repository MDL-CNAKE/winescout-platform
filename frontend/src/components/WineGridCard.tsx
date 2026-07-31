/**
 * Card del catalogo in griglia.
 *
 * Gerarchia: bottiglia, riga con lotto e preferito, titolo in serif,
 * descrizione derivata dai dati, prezzo e azione. La descrizione non e'
 * testo redazionale: e' costruita dai valori chimici del vino, come tutto
 * il resto del catalogo.
 */
import { Link } from "@tanstack/react-router";
import { BottleIcon } from "./BottleIcon";
import type { Wine } from "../api";
import {
  wineTitle,
  wineLot,
  alcoholDescriptor,
  sugarDescriptor,
  mainPairing,
} from "../lib/wineLabel";

function description(w: Wine): string {
  const corpo = alcoholDescriptor(w.alcohol);
  const dolcezza = sugarDescriptor(w.residual_sugar, w.fixed_acidity);
  const tipo = w.type === "red" ? "rosso" : "bianco";
  const base = `Un ${tipo} ${corpo}, ${dolcezza}, ${w.alcohol.toFixed(1)}% vol con pH ${w.ph.toFixed(2)}.`;
  const pairing = mainPairing(w);
  return pairing ? `${base} Da provare con ${pairing.toLowerCase()}.` : base;
}

/** Iniziali del nome, per l'indicatore compatto sulle card. */
function initials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w.charAt(0).toUpperCase())
    .join("");
}

interface WineGridCardProps {
  wine: Wine;
  isFavorite: boolean;
  onToggleFavorite: (id: number) => void;
  /** Colleghi che hanno segnato lo stesso vino. */
  others?: { operator_id: number; operator_name: string }[];
}

export function WineGridCard({
  wine,
  isFavorite,
  onToggleFavorite,
  others = [],
}: WineGridCardProps) {
  const lot = wineLot(wine.name);
  const title = wineTitle(wine.name);

  return (
    <article className="grid-card">
      <Link
        to="/vino/$wineId"
        params={{ wineId: String(wine.id) }}
        className="grid-card-figure"
        aria-label={`Apri la scheda di ${title}`}
      >
        <BottleIcon wine={wine} size={150} />
      </Link>

      <div className="grid-card-top">
        <span className="grid-card-lot">
          {lot ? `Lotto ${lot}` : wine.type === "red" ? "Rosso" : "Bianco"}
        </span>
        <span className="grid-card-fav-group">
          {others.length > 0 && (
            <span
              className="grid-card-others"
              title={`Segnato anche da: ${others.map((o) => o.operator_name).join(", ")}`}
            >
              {others.slice(0, 3).map((o) => (
                <span key={o.operator_id} className="grid-card-initial">
                  {initials(o.operator_name)}
                </span>
              ))}
              {others.length > 3 && <span className="grid-card-initial">+{others.length - 3}</span>}
            </span>
          )}
        <button
          type="button"
          className={`grid-card-fav${isFavorite ? " active" : ""}`}
          onClick={() => onToggleFavorite(wine.id)}
          aria-pressed={isFavorite}
          aria-label={isFavorite ? `Rimuovi ${title} dai preferiti` : `Aggiungi ${title} ai preferiti`}
        >
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
            <path
              d="M12 20.5 3.8 12.3a5 5 0 0 1 7.1-7.1l1.1 1.1 1.1-1.1a5 5 0 1 1 7.1 7.1z"
              fill={isFavorite ? "currentColor" : "none"}
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinejoin="round"
            />
          </svg>
        </button>
        </span>
      </div>

      <h3 className="grid-card-title">{title}</h3>
      <p className="grid-card-desc">{description(wine)}</p>

      <div className="grid-card-footer">
        <span className="grid-card-price">
          {wine.price_eur != null ? `${wine.price_eur.toFixed(2).replace(".", ",")} €` : "—"}
        </span>
        <Link to="/vino/$wineId" params={{ wineId: String(wine.id) }} className="grid-card-cta">
          Scopri
        </Link>
      </div>
    </article>
  );
}
