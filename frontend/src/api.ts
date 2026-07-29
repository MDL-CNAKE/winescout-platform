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

export const predictQuality = (input: PredictionInput) =>
  api.post<{ quality: number }>("/api/predict", input).then((res) => res.data);

export const fetchRecommendations = (wineId: number) =>
  api.get<Recommendation[]>(`/api/recommend/${wineId}`).then((res) => res.data);

export const fetchCheaperAlternatives = (wineId: number) =>
  api
    .get<CheaperAlternative[]>(`/api/recommend/${wineId}/cheaper`)
    .then((res) => res.data);

export const askSommelier = (question: string, wineId: number | null) =>
  api
    .post<SommelierResponse>("/api/sommelier", { question, wine_id: wineId })
    .then((res) => res.data);
