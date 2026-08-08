/**
 * Operatore corrente, condiviso da tutta l'applicazione.
 *
 * Prima questo stato viveva dentro useFavorites con un useState locale.
 * Siccome l'hook viene chiamato da piu' componenti — l'intestazione per
 * decidere quali sezioni mostrare, il selettore per cambiarlo — ognuno
 * aveva una copia separata: cambiando operatore si aggiornava solo il
 * selettore, e la navigazione restava indietro fino al ricaricamento della
 * pagina.
 *
 * Sollevandolo in un contesto esiste una sola copia e tutti i componenti
 * che la leggono si aggiornano insieme.
 */
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

const STORAGE_KEY = "cruscout.operator";

interface Valore {
  operatorId: number | null;
  setOperatorId: (id: number | null) => void;
}

const OperatoreContext = createContext<Valore | null>(null);

function leggiSalvato(): number | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? Number(raw) : null;
  } catch {
    // localStorage puo' essere disabilitato: la scelta vale per la sessione.
    return null;
  }
}

export function OperatoreProvider({ children }: { children: ReactNode }) {
  const [operatorId, setOperatorId] = useState<number | null>(leggiSalvato);

  useEffect(() => {
    if (operatorId === null) return;
    try {
      localStorage.setItem(STORAGE_KEY, String(operatorId));
    } catch {
      /* storage non disponibile: si prosegue in memoria */
    }
  }, [operatorId]);

  return (
    <OperatoreContext.Provider value={{ operatorId, setOperatorId }}>
      {children}
    </OperatoreContext.Provider>
  );
}

export function useOperatore(): Valore {
  const ctx = useContext(OperatoreContext);
  if (!ctx) {
    throw new Error("useOperatore va usato dentro OperatoreProvider");
  }
  return ctx;
}
