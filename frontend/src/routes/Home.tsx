/**
 * Landing page: marchio al centro, headline, descrizione. Gerarchia
 * ridotta a quattro livelli (nome, payoff, headline, testo) e una sola
 * lingua, per non frammentare la lettura.
 */
export function Home() {
  return (
    <section className="home-hero">
      <div className="brand-block">
        <h1 className="brand-name">Bacchus</h1>
      </div>

      <p className="home-claim">
        Dagli algoritmi al calice.<br />
        Senza storie di fantasia.
      </p>
      <p className="home-desc">
        Analizziamo profilo chimico, qualità e abbinamenti con modelli predittivi, per darti solo
        dati reali su ciò che troverai nel bicchiere.
      </p>
    </section>
  );
}
