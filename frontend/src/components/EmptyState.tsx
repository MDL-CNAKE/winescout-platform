/**
 * Stato vuoto o di attesa, con il sommelier come presenza ricorrente.
 *
 * Serve a evitare che un filtro senza risultati o un caricamento appaiano
 * come una pagina rotta: il personaggio da' continuita' visiva fra le
 * sezioni e rende esplicito che il sistema sta funzionando.
 */
import { RobotSommelierIcon } from "./RobotSommelierIcon";

interface EmptyStateProps {
  title: string;
  hint?: string;
  /** Attenua la figura: usato durante i caricamenti, dove non c'e' nulla
   *  da segnalare all'utente se non l'attesa. */
  loading?: boolean;
}

export function EmptyState({ title, hint, loading = false }: EmptyStateProps) {
  return (
    <div className={`empty-state${loading ? " loading" : ""}`}>
      <RobotSommelierIcon size={110} />
      <p className="empty-state-title">{title}</p>
      {hint && <p className="caption">{hint}</p>}
    </div>
  );
}
