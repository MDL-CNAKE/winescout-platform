/**
 * Selettore dell'operatore corrente e del suo ruolo.
 *
 * Non e' un login: l'applicazione appartiene a una sola cantina e chiunque
 * la apra puo' dichiararsi chiunque. Serve a due cose — distinguere le
 * selezioni di lavoro fra colleghi, e mostrare a ciascuno gli strumenti del
 * proprio mestiere invece di tutti insieme.
 *
 * Vive nell'intestazione e non in una pagina, perche' il ruolo governa la
 * navigazione: doverlo cambiare tornando alla home sarebbe scomodo.
 */
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createOperator, type Ruolo } from "../api";
import { useFavorites } from "../hooks/useFavorites";

const RUOLI: { value: Ruolo; label: string }[] = [
  { value: "titolare", label: "Titolare" },
  { value: "enologo", label: "Enologo" },
  { value: "vendite", label: "Vendite" },
  { value: "logistica", label: "Logistica" },
];

export function OperatorPicker() {
  const { operators, operatorId, setOperatorId } = useFavorites();
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const [role, setRole] = useState<Ruolo>("titolare");
  const queryClient = useQueryClient();

  const create = useMutation({
    mutationFn: () => createOperator(name.trim(), role),
    onSuccess: (op) => {
      queryClient.invalidateQueries({ queryKey: ["operators"] });
      setOperatorId(op.id);
      setName("");
      setAdding(false);
    },
  });

  if (!operators) return null;

  const corrente = operators.find((o) => o.id === operatorId);

  return (
    <div className="operator-picker">
      <label>
        <span className="operator-label">Operatore</span>
        <select value={operatorId ?? ""} onChange={(e) => setOperatorId(Number(e.target.value))}>
          {operators.map((o) => (
            <option key={o.id} value={o.id}>
              {o.name}
            </option>
          ))}
        </select>
      </label>

      {/* Il ruolo si mostra solo quando aggiunge informazione: se coincide
          con il nome dell'operatore sarebbe un doppione. */}
      {corrente && corrente.name.toLowerCase() !== corrente.role && (
        <span className="operator-ruolo">· {etichettaRuolo(corrente.role)}</span>
      )}

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
          <select value={role} onChange={(e) => setRole(e.target.value as Ruolo)}>
            {RUOLI.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
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

function etichettaRuolo(r: Ruolo): string {
  return RUOLI.find((x) => x.value === r)?.label ?? r;
}
