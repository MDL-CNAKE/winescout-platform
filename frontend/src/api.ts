/**
 * Client API: un unico punto che parla con il backend FastAPI.
 * Se cambia l'indirizzo del backend (es. in produzione), va aggiornato
 * solo qui grazie alla variabile d'ambiente VITE_API_URL.
 */
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const api = axios.create({ baseURL: API_URL });

export interface Wine {
  id: number;
  name: string;
  type: "red" | "white";
  alcohol: number;
  ph: number;
  residual_sugar: number;
  fixed_acidity: number;
  volatile_acidity: number;
  chlorides: number;
  sulphates: number;
  quality: number;
  price_eur: number | null;
  margin_pct: number | null;
  food_pairing: string | null;
}

export interface PredictionInput {
  type: "red" | "white";
  fixed_acidity: number;
  volatile_acidity: number;
  citric_acid: number;
  residual_sugar: number;
  chlorides: number;
  free_sulfur_dioxide: number;
  total_sulfur_dioxide: number;
  density: number;
  ph: number;
  sulphates: number;
  alcohol: number;
}

export interface Recommendation {
  id: number;
  name: string;
  type: string;
  alcohol: number;
  ph: number;
  quality: number;
  price_eur: number;
  similarity: number;
}

export interface CheaperAlternative extends Recommendation {
  savings_pct: number;
}

export interface SommelierResponse {
  answer: string;
  demo_mode: boolean;
  sources: string[];
}

export const fetchWines = () =>
  api.get<Wine[]>("/api/wines").then((res) => res.data);

/** Elenco leggero per le liste di navigazione (solo id, nome, tipo). */
export interface WineSummary {
  id: number;
  name: string;
  type: "red" | "white";
}

export const fetchWinesSummary = () =>
  api.get<WineSummary[]>("/api/wines/summary").then((res) => res.data);

export const fetchWine = (wineId: number) =>
  api.get<Wine>(`/api/wines/${wineId}`).then((res) => res.data);

/** Estremi reali del catalogo, per tarare i cursori dei filtri. */
export interface WineFacets {
  alcohol: [number, number];
  residual_sugar: [number, number];
  fixed_acidity: [number, number];
  price_eur: [number, number];
  quality: [number, number];
}

export const fetchWineFacets = () =>
  api.get<WineFacets>("/api/wines/facets").then((res) => res.data);

export type SortOption =
  | "quality_desc"
  | "quality_asc"
  | "price_asc"
  | "price_desc"
  | "alcohol_desc"
  | "name_asc";

export interface WineQuery {
  type?: "red" | "white" | null;
  min_quality?: number | null;
  min_alcohol?: number | null;
  max_alcohol?: number | null;
  min_sugar?: number | null;
  max_sugar?: number | null;
  min_acidity?: number | null;
  max_acidity?: number | null;
  min_price?: number | null;
  max_price?: number | null;
  sort?: SortOption;
  page?: number;
  page_size?: number;
}

export interface WineSearchResult {
  items: Wine[];
  total: number;
  page: number;
  page_size: number;
}

export const searchWines = (query: WineQuery) => {
  // I parametri nulli non vengono inviati: il backend li interpreta come
  // "filtro non applicato".
  const params = Object.fromEntries(
    Object.entries(query).filter(([, v]) => v !== null && v !== undefined)
  );
  return api
    .get<WineSearchResult>("/api/wines/search", { params })
    .then((res) => res.data);
};

export const predictQuality = (input: PredictionInput) =>
  api.post<{ quality: number }>("/api/predict", input).then((res) => res.data);

export const fetchRecommendations = (wineId: number) =>
  api.get<Recommendation[]>(`/api/recommend/${wineId}`).then((res) => res.data);

export const fetchCheaperAlternatives = (wineId: number) =>
  api
    .get<CheaperAlternative[]>(`/api/recommend/${wineId}/cheaper`)
    .then((res) => res.data);

/* --- Predisposizione alla conservazione -------------------------------- */

export interface Indicatore {
  nome: string;
  valore: number;
  unita: string;
  livello: "buono" | "attenzione" | "critico";
  spiegazione: string;
}

export interface ConservazioneRiga {
  id: number;
  name: string;
  type: "red" | "white";
  quality: number;
  price_eur: number | null;
  punteggio: number;
  giudizio: string;
}

export interface Conservazione extends ConservazioneRiga {
  indicatori: Indicatore[];
}

export const fetchConservazione = (type?: "red" | "white" | null, limit = 60) =>
  api
    .get<ConservazioneRiga[]>("/api/conservazione", {
      params: { ...(type ? { type } : {}), limit },
    })
    .then((res) => res.data);

export const fetchConservazioneVino = (wineId: number) =>
  api.get<Conservazione>(`/api/conservazione/${wineId}`).then((res) => res.data);

/* --- Selezioni di lavoro condivise ------------------------------------ */

export interface Operator {
  id: number;
  name: string;
}

export interface Favorite {
  wine_id: number;
  operator_id: number;
  operator_name: string;
}

export const fetchOperators = () =>
  api.get<Operator[]>("/api/operators").then((res) => res.data);

export const createOperator = (name: string) =>
  api.post<Operator>("/api/operators", { name }).then((res) => res.data);

export const fetchFavorites = () =>
  api.get<Favorite[]>("/api/favorites").then((res) => res.data);

export const addFavorite = (wineId: number, operatorId: number) =>
  api.post("/api/favorites", { wine_id: wineId, operator_id: operatorId });

export const removeFavorite = (wineId: number, operatorId: number) =>
  api.delete("/api/favorites", { params: { wine_id: wineId, operator_id: operatorId } });

export const askSommelier = (question: string, wineId: number | null) =>
  api
    .post<SommelierResponse>("/api/sommelier", { question, wine_id: wineId })
    .then((res) => res.data);

export interface PackagingItem {
  id: number;
  name: string;
  type: "red" | "white";
  quality: number;
  price_eur: number | null;
  style: "Moderno" | "Classico" | "Young" | "Elegante";
  bottle_format: string;
  cap_type: string;
  label_material: string;
}

export const fetchPackaging = () =>
  api.get<PackagingItem[]>("/api/packaging").then((res) => res.data);

export const fetchPackagingItem = (wineId: number) =>
  api.get<PackagingItem>(`/api/packaging/${wineId}`).then((res) => res.data);
