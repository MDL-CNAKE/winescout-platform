/**
 * Selezioni di lavoro condivise fra gli operatori della cantina.
 *
 * Le preferenze stanno nel database, non nel browser: cosi' sono le stesse
 * per chiunque apra l'applicazione dalla stessa installazione, e ogni riga
 * porta il nome di chi l'ha messa. Nel browser resta solo l'identita'
 * dichiarata dall'operatore corrente (chi sto usando l'app in questo
 * momento), che non e' un'autenticazione ma una scelta da un elenco.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchOperators,
  fetchFavorites,
  addFavorite,
  removeFavorite,
  type Favorite,
} from "../api";

const OPERATOR_KEY = "cruscout.operator";

function readStoredOperator(): number | null {
  try {
    const raw = localStorage.getItem(OPERATOR_KEY);
    return raw ? Number(raw) : null;
  } catch {
    return null;
  }
}

export function useFavorites() {
  const queryClient = useQueryClient();
  const [operatorId, setOperatorId] = useState<number | null>(readStoredOperator);

  const { data: operators } = useQuery({ queryKey: ["operators"], queryFn: fetchOperators });
  const { data: favorites } = useQuery({ queryKey: ["favorites"], queryFn: fetchFavorites });

  // Se non e' stato scelto nessun operatore (primo avvio) si seleziona il
  // primo dell'elenco, cosi' l'interfaccia e' subito utilizzabile.
  useEffect(() => {
    if (operatorId === null && operators && operators.length > 0) {
      setOperatorId(operators[0].id);
    }
  }, [operatorId, operators]);

  useEffect(() => {
    if (operatorId === null) return;
    try {
      localStorage.setItem(OPERATOR_KEY, String(operatorId));
    } catch {
      /* storage non disponibile: la scelta vale solo per questa sessione */
    }
  }, [operatorId]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["favorites"] });
  const add = useMutation({ mutationFn: (w: number) => addFavorite(w, operatorId!), onSuccess: invalidate });
  const drop = useMutation({ mutationFn: (w: number) => removeFavorite(w, operatorId!), onSuccess: invalidate });

  /** Selezioni raggruppate per vino, per non ricalcolarle a ogni card. */
  const byWine = useMemo(() => {
    const map = new Map<number, Favorite[]>();
    for (const f of favorites ?? []) {
      const list = map.get(f.wine_id);
      if (list) list.push(f);
      else map.set(f.wine_id, [f]);
    }
    return map;
  }, [favorites]);

  const isFavorite = useCallback(
    (wineId: number) =>
      operatorId !== null &&
      (byWine.get(wineId) ?? []).some((f) => f.operator_id === operatorId),
    [byWine, operatorId]
  );

  /** Colleghi che hanno segnato il vino, escluso l'operatore corrente. */
  const othersFor = useCallback(
    (wineId: number) =>
      (byWine.get(wineId) ?? []).filter((f) => f.operator_id !== operatorId),
    [byWine, operatorId]
  );

  const toggle = useCallback(
    (wineId: number) => {
      if (operatorId === null) return;
      if (isFavorite(wineId)) drop.mutate(wineId);
      else add.mutate(wineId);
    },
    [operatorId, isFavorite, add, drop]
  );

  return { operators, operatorId, setOperatorId, isFavorite, othersFor, toggle };
}
