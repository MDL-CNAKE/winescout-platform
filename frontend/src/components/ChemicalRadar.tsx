/**
 * Radar del profilo chimico: normalizza ogni caratteristica su una scala
 * 0-100 (usando i range tipici del dataset UCI Wine Quality) cosi' assi
 * con unita' di misura diverse (pH vs mg/L di cloruri) sono confrontabili
 * sullo stesso grafico.
 */
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import type { Wine } from "../api";

const RANGES: Record<string, [number, number]> = {
  "Alcol": [8, 15],
  "pH": [2.7, 4.0],
  "Acidità fissa": [4, 16],
  "Acidità volatile": [0.1, 1.6],
  "Cloruri": [0.01, 0.6],
  "Solfati": [0.3, 2.0],
};

function normalize(value: number, [min, max]: [number, number]): number {
  const pct = ((value - min) / (max - min)) * 100;
  return Math.max(0, Math.min(100, pct));
}

export function ChemicalRadar({ wine }: { wine: Wine }) {
  const data = [
    { asse: "Alcol", valore: normalize(wine.alcohol, RANGES["Alcol"]) },
    { asse: "pH", valore: normalize(wine.ph, RANGES["pH"]) },
    { asse: "Acidità fissa", valore: normalize(wine.fixed_acidity, RANGES["Acidità fissa"]) },
    { asse: "Acidità volatile", valore: normalize(wine.volatile_acidity, RANGES["Acidità volatile"]) },
    { asse: "Cloruri", valore: normalize(wine.chlorides, RANGES["Cloruri"]) },
    { asse: "Solfati", valore: normalize(wine.sulphates, RANGES["Solfati"]) },
  ];

  return (
    <div className="radar-wrapper">
      <ResponsiveContainer width="100%" height={260}>
        <RadarChart data={data}>
          <PolarGrid stroke="#e0d5c0" />
          <PolarAngleAxis dataKey="asse" tick={{ fill: "#555", fontSize: 11 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
          <Radar dataKey="valore" stroke="#6d1b2f" fill="#6d1b2f" fillOpacity={0.35} />
        </RadarChart>
      </ResponsiveContainer>
      <p className="caption">
        Profilo chimico normalizzato sui range tipici del dataset (0-100%),
        non valori assoluti — utile per confrontare la "forma" di vini diversi.
      </p>
    </div>
  );
}
