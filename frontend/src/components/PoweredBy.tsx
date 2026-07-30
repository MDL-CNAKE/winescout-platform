/**
 * Firma dell'autrice, sopra le note tecniche del footer.
 *
 * L'ovale attorno a "She" riprende il motivo grafico gia' usato dal
 * marchio (la testa del sommelier e' un ovale bordato d'oro), cosi' la
 * firma appartiene all'identita' del sito invece di sembrarci appiccicata
 * sopra.
 */
export function PoweredBy() {
  return (
    <div className="powered-by">
      <span className="powered-by-label">Powered by</span>
      <span className="powered-by-name">
        <span className="powered-by-she">She</span>
        <span className="powered-by-co">and Co</span>
      </span>
    </div>
  );
}
