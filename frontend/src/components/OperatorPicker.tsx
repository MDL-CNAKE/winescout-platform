/**
 * Selettore dell'operatore corrente.
 *
 * Non e' un login: l'applicazione appartiene a una sola cantina e chiunque
 * la apra puo' dichiararsi chiunque. Serve unicamente a distinguere le
 * selezioni di lavoro fra colleghi che usano la stessa installazione.
 */
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createOperator } from "../api";
import { useFavorites } from "../hooks/useFavorites";

export function OperatorPicker() {
  const { operators, operatorId, setOperatorId } = useFavorites();
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const queryClient = useQueryClient();

  const create = useMutation({
    mutationFn: () => createOperator(name.trim()),
    onSuccess: (op) => {
      queryClient.invalidateQueries({ queryKey: ["operators"] });
      setOperatorId(op.id);
      setName("");
      setAdding(false);
    },
  });

  if (!operators) return null;

  return (
    <div className="operator-picker">
      <label>
        <span className="operator-label">Operatore</span>
        <select
          value={operatorId ?? ""}
          onChange={(e) => setOperatorId(Number(e.target.value))}
        >
          {operators.map((o) => (
            <option key={o.id} value={o.id}>
              {o.name}
            </option>
          ))}
        </select>
      </label>

      {adding ? (
        <span className="operator-add">
          <input
            type="text"
            value={name}
            maxLength={60}
            placeholder="Nome o ruolo"
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && name.trim() && create.mutate()}
          />
          <button
            type="button"
            className="operator-confirm"
            onClick={() => create.mutate()}
            disabled={!name.trim() || create.isPending}
          >
            Aggiungi
          </button>
          <button type="button" className="operator-cancel" onClick={() => setAdding(false)}>
            Annulla
          </button>
        </span>
      ) : (
        <button type="button" className="operator-cancel" onClick={() => setAdding(true)}>
          + Nuovo
        </button>
      )}

      {create.isError && <span className="error">Nome già presente.</span>}
    </div>
  );
}
