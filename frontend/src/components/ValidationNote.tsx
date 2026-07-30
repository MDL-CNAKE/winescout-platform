/**
 * Nota di validazione mostrata sotto predizione e raccomandazioni.
 *
 * Dichiara i numeri reali della validazione INSIEME al loro limite: R2 0.56
 * significa che il modello spiega poco piu' della meta' della varianza, e
 * che sugli estremi della scala (vini scadenti o eccellenti, rarissimi nel
 * dataset) e' meno affidabile. Dirlo qui, dove l'utente legge il risultato,
 * evita che un numero modesto venga scambiato per una certezza.
 *
 * Fonti dei valori: src/models/compare_models.py (5-fold CV) e
 * src/models/train.py (test set indipendente 20%).
 */
type Kind = "predizione" | "raccomandazione";

export function ValidationNote({ kind }: { kind: Kind }) {
  return (
    <p className="validation-note">
      {kind === "predizione" ? (
        <>
          <strong>Come leggere questo punteggio.</strong> RandomForest addestrato su 6.497
          vini, validato con 5-fold cross-validation (R² medio 0,52) e su un test set
          indipendente del 20% (R² 0,56; RMSE 0,57). Il modello spiega poco più della metà
          della variabilità: coglie bene la tendenza generale, meno gli estremi della scala,
          dove il dataset contiene pochissimi esempi. È un supporto decisionale, non una
          valutazione sostitutiva di quella di un sommelier.
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
