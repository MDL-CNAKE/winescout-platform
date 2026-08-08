/**
 * Costo e tempi della risposta appena generata.
 *
 * I due tempi restano separati: aggregati in un numero solo non direbbero
 * dove intervenire. Se domina il recupero si lavora sull'indice, se domina
 * la generazione si agisce su modello, lunghezza della risposta o cache.
 *
 * I token del prompt sono quasi tutti prompt di sistema — i guardrail di
 * SVEVA sono lunghi — quindi quel numero e' il costo fisso di ogni domanda,
 * utile a decidere se vale la pena accorciarli.
 */
import type { MetricheLLM } from "../api";

export function MetricheRisposta({ metriche }: { metriche: MetricheLLM | null }) {
  if (!metriche) return null;

  const voci: { valore: string; etichetta: string }[] = [];

  if (metriche.ms_recupero != null) {
    voci.push({ valore: `${metriche.ms_recupero} ms`, etichetta: "recupero" });
  }
  if (metriche.ms_generazione != null) {
    voci.push({
      valore:
        metriche.ms_generazione >= 1000
          ? `${(metriche.ms_generazione / 1000).toFixed(1)} s`
          : `${metriche.ms_generazione} ms`,
      etichetta: "generazione",
    });
  }
  if (metriche.token_prompt != null) {
    voci.push({ valore: String(metriche.token_prompt), etichetta: "token prompt" });
  }
  if (metriche.token_risposta != null) {
    voci.push({ valore: String(metriche.token_risposta), etichetta: "token risposta" });
  }

  if (voci.length === 0) return null;

  return (
    <div className="metriche">
      <ul className="metriche-lista">
        {voci.map((v) => (
          <li key={v.etichetta}>
            <span className="metriche-valore">{v.valore}</span>
            <span className="metriche-etichetta">{v.etichetta}</span>
          </li>
        ))}
      </ul>
      {metriche.modello && <p className="metriche-modello">{metriche.modello}</p>}
    </div>
  );
}
