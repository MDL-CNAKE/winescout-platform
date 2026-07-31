/**
 * Etichette derivate (purtroppo) dai dati reali.
 *
 * I nomi in database hanno forma "Rosso Equilibrato Amabile - Lotto #0002":
 * il lotto serve a distinguere referenze altrimenti identiche, ma ripeterlo
 * nel titolo E nel badge sulla foto e' ridondante. Qui separiamo le due
 * informazioni cosi' ogni componente mostra solo quella che gli serve.
 */
import type { Wine } from "../api";

const LOT_RE = /\s*-\s*Lotto\s*#(\d+)\s*$/i;

/** Nome senza il suffisso del lotto: "Rosso Equilibrato Amabile". */
export function wineTitle(name: string): string {
  return name.replace(LOT_RE, "").trim();
}

/** Solo il codice di lotto, se presente: "#0002". */
export function wineLot(name: string): string | null {
  const match = name.match(LOT_RE);
  return match ? `#${match[1]}` : null;
}

export function alcoholDescriptor(alcohol: number): string {
  if (alcohol >= 12.0) return "corposo";
  if (alcohol <= 9.5) return "leggero";
  return "equilibrato";
}

/**
 * Dolcezza secondo il Reg. UE 2019/33, con la correzione per l'acidita':
 * a parita' di zucchero un vino piu' acido e' percepito piu' secco.
 * Stesse soglie di src/wine_style.py lato backend.
 */
export function sugarDescriptor(sugar: number, acidity: number): string {
  if (sugar <= 4 || (sugar <= 9 && acidity >= sugar - 2)) return "secco";
  if (sugar <= 12 || (sugar <= 18 && acidity >= sugar - 10)) return "abboccato";
  if (sugar <= 45) return "amabile";
  return "dolce";
}

/**
 * Un piatto della lista di abbinamento, a rotazione sull'id del vino
 *
 * Le regole in src/pairing.py classificano 6497 vini in 7 fasce
 *
 * E' una mitigazione di presentazione, non risolve la granularita' delle
 * regole: vedi docs/model_limitations.md
 */
export function mainPairing(wine: Wine): string | null {
  if (!wine.food_pairing) return null;
  const dishes = wine.food_pairing
    .split(",")
    .map((d) => d.split("(")[0].trim())
    .filter(Boolean);
  if (dishes.length === 0) return null;
  return dishes[wine.id % dishes.length];
}

/** Lista completa degli abbinamenti, per la scheda di dettaglio. */
export function allPairings(wine: Wine): string[] {
  if (!wine.food_pairing) return [];
  return wine.food_pairing.split(",").map((d) => d.trim()).filter(Boolean);
}
