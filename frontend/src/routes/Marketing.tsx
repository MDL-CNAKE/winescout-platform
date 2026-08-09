/**
 * Marketing e strategia — sezione in arrivo.
 *
 * Questa pagina è deliberatamente diversa da Spedizioni, che è un semplice
 * segnaposto. Qui le funzioni mancano per una ragione precisa: **i dati non
 * esistono**. WineScout conosce la chimica dei lotti, la qualità e un prezzo
 * derivato. Non conosce un solo ordine, cliente, canale o data di vendita.
 *
 * La tentazione sarebbe costruire comunque un cruscotto — fatturato, ordini,
 * vendite per ora, metodo di pagamento — riempiendolo di numeri plausibili.
 * Sarebbe lo stesso errore che il progetto ha rifiutato altrove: inventare
 * vitigni che il dataset non contiene, o dedurre preferenze di mercato da
 * dati che non le contengono.
 *
 * Quindi ogni voce dichiara **quale dato le servirebbe**. Così la pagina è
 * utile anche da vuota: non promette una funzione futura, dice al titolare
 * cosa deve cominciare a registrare per poterla avere. È una specifica, non
 * un annuncio.
 */

type Funzione = {
  titolo: string;
  cosa: string;
  richiede: string;
  stato: "manca" | "parziale";
};

const FUNZIONI: Funzione[] = [
  {
    titolo: "Andamento del venduto",
    cosa: "Come si muovono ricavi e volumi nel tempo, per mese e per stagione.",
    richiede:
      "Registro ordini con data, referenza, quantità e importo. Nel database non esiste nessuna tabella di vendite.",
    stato: "manca",
  },
  {
    titolo: "Referenze che tirano",
    cosa: "Quali lotti si vendono davvero, non quali sono i migliori in analisi.",
    richiede:
      "Storico ordini per referenza. Oggi il catalogo può essere ordinato per qualità e prezzo, che sono altra cosa: un vino ottimo che nessuno compra resterebbe in cima.",
    stato: "manca",
  },
  {
    titolo: "Marginalità per fascia",
    cosa: "Dove si guadagna davvero: quale fascia di prezzo rende, al netto dei volumi.",
    richiede:
      "Costi di produzione per lotto e quantità vendute. La colonna margine esistente è una stima derivata dal prezzo, non un margine misurato.",
    stato: "parziale",
  },
  {
    titolo: "Canali di vendita",
    cosa: "Quanto pesano enoteca, ristorazione, vendita diretta e online.",
    richiede:
      "Un campo canale su ogni ordine. Il dato non è deducibile da nulla di ciò che la piattaforma già conosce.",
    stato: "manca",
  },
  {
    titolo: "Composizione del catalogo",
    cosa: "Come si distribuisce l'offerta per fascia di prezzo, qualità e tipologia.",
    richiede:
      "Nulla: questi dati ci sono già. È l'unica analisi di questo elenco realizzabile oggi, e arriverà per prima.",
    stato: "parziale",
  },
  {
    titolo: "Stagionalità degli abbinamenti",
    cosa: "Quali abbinamenti vengono chiesti a SVEVA e in quale periodo dell'anno.",
    richiede:
      "Registrazione delle domande poste al sommelier. Oggi non vengono salvate — scelta deliberata di riservatezza, che andrebbe riconsiderata esplicitamente e dichiarata a chi usa la piattaforma.",
    stato: "manca",
  },
];

export function Marketing() {
  return (
    <section className="marketing">
      <h2>Marketing e strategia</h2>
      <p className="marketing-claim">In arrivo</p>

      <p className="hint">
        Le analisi commerciali non ci sono ancora, e non per mancanza di tempo: la
        piattaforma conosce la chimica dei lotti, non le vendite. Sotto trovi cosa
        servirebbe per ciascuna, così la cantina sa da dove cominciare.
      </p>

      <ul className="funzioni-mancanti">
        {FUNZIONI.map((f) => (
          <li key={f.titolo} className={`funzione stato-${f.stato}`}>
            <h3>{f.titolo}</h3>
            <p>{f.cosa}</p>
            <p className="funzione-richiede">
              <span className="funzione-etichetta">
                {f.stato === "parziale" ? "Dato parziale" : "Dato mancante"}
              </span>
              {f.richiede}
            </p>
          </li>
        ))}
      </ul>

      <p className="caption">
        Nel frattempo il catalogo si può filtrare ed esportare in CSV dalla home: i dati
        che la piattaforma possiede davvero sono già disponibili per essere analizzati
        con gli strumenti che usi — Excel, Power Query, un foglio di calcolo qualsiasi.
      </p>
    </section>
  );
}
