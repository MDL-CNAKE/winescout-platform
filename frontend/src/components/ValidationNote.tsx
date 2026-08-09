/**
 * Nota di validazione mostrata sotto predizione e raccomandazioni.
 *
 * Dichiara i numeri reali della validazione INSIEME al loro limite. Dirlo
 * qui, dove l'utente legge il risultato, evita che un numero modesto venga
 * scambiato per una certezza.
 *
 * I valori sono stati CORRETTI AL RIBASSO. Fino a poco fa questa nota
 * dichiarava R2 0.52 in cross-validation e 0.56 su test: erano gonfiati
 * perche' il dataset contiene 1.177 righe duplicate su 6.497 e lo split
 * casuale ne mandava una in addestramento e la copia in test (vedi
 * docs/model_limitations.md). Con valutazione raggruppata i valori reali sono
 * 0.385 e 0.397.
 *
 * Abbassare un numero mostrato all'utente e' l'unica scelta possibile quando
 * si scopre che era sbagliato, ma vale la pena notare che era anche il caso
 * piu' urgente: una metrica gonfiata in un file di ricerca inganna chi valuta
 * il progetto, la stessa metrica in questa nota inganna una cantina che deve
 * decidere quanto fidarsi.
 *
 * Fonti dei valori: src/models/compare_models.py (CV raggruppata) e
 * src/models/train.py (test set senza copie condivise).
 */
type Kind = "predizione" | "raccomandazione";

export function ValidationNote({ kind }: { kind: Kind }) {
  return (
    <p className="validation-note">
      {kind === "predizione" ? (
        <>
          <strong>Come leggere questo punteggio.</strong> RandomForest addestrato su 6.497
          vini, validato con 5-fold cross-validation raggruppata (R² medio 0,39) e su un
          test set del 20% senza righe ripetute (R² 0,40; RMSE 0,68). Il modello spiega
          circa il 40% della variabilità: coglie la tendenza generale, molto meno gli
          estremi della scala, dove il dataset contiene pochissimi esempi — il 77% dei vini
          sta in due sole classi su undici. È un supporto decisionale, non una valutazione
          sostitutiva di quella di un sommelier.
        </>
      ) : (
        <>
          <strong>Su cosa si basano.</strong> Similarità coseno sulle sole feature chimiche
          dei 6.497 vini del dataset: il sistema propone vini con profilo analitico vicino,
          non vini che uno stesso cliente ha gradito. Annata, terroir e affinamento non sono
          presenti nei dati e quindi non entrano nel calcolo.
        </>
      )}
    </p>
  );
}
