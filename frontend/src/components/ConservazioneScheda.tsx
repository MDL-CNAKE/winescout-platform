/**
 * Scheda di conservazione di un vino: punteggio sintetico e, sempre
 * visibili accanto, i quattro indicatori con la loro spiegazione.
 *
 * Il punteggio serve a ordinare il catalogo, ma da solo non direbbe alla
 * cantina cosa fare: sono i singoli parametri a indicare se il problema e'
 * la solforosa (correggibile) o l'acidita' volatile (difetto conclamato).
 * Per questo non sono nascosti dietro un espansore.
 */
import { useQuery } from "@tanstack/react-query";
import { fetchConservazioneVino } from "../api";

export function ConservazioneScheda({ wineId }: { wineId: number }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["conservazione", wineId],
    queryFn: () => fetchConservazioneVino(wineId),
    retry: false,
  });

  if (isLoading) return <p>Calcolo degli indicatori...</p>;
  if (isError || !data) return <p className="error">Indicatori non disponibili.</p>;

  return (
    <>
      <div className={`cons-verdict livello-${verdictLevel(data.punteggio)}`}>
        <span className="cons-score">{data.punteggio}<small>/100</small></span>
        <div>
          <h3>{data.giudizio}</h3>
          <p className="caption">
            Indice di resistenza a ossidazione e alterazione microbica, calcolato
            da parametri enologici. Non riguarda l'evoluzione organolettica.
          </p>
        </div>
      </div>

      <ul className="cons-list">
        {data.indicatori.map((i) => (
          <li key={i.nome} className={`cons-item livello-${i.livello}`}>
            <div className="cons-item-head">
              <span className="cons-item-name">{i.nome}</span>
              <span className="cons-item-value">
                {i.valore}
                {i.unita && <> {i.unita}</>}
              </span>
            </div>
            <p className="cons-item-text">{i.spiegazione}</p>
          </li>
        ))}
      </ul>

      <p className="validation-note">
        <strong>Come leggere questo indice.</strong> Non è un modello addestrato:
        il dataset non contiene alcuna informazione su come i vini si siano
        evoluti nel tempo, quindi non esiste una verità di riferimento su cui
        addestrare o misurare un'accuratezza. È un sistema a regole costruito su
        parametri enologici consolidati, ispezionabile riga per riga. Mancano
        tannini, polifenoli ed estratto secco: per questo l'indice parla di
        stabilità chimica e non di potenziale di invecchiamento, che per i rossi
        dipende soprattutto dalla struttura fenolica.
      </p>
    </>
  );
}

function verdictLevel(punteggio: number): string {
  if (punteggio >= 75) return "buono";
  if (punteggio >= 45) return "attenzione";
  return "critico";
}
