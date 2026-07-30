/**
 * Landing page.
 *
 * Il marchio vive solo nella navbar e l'hero parte dal claim, che e' la cosa da
 * leggere per prima, e si chiude con una CTA.
 */
import { Link } from "@tanstack/react-router";

export function Home() {
  return (
    <section className="home-hero">
      <h1 className="home-claim">Dagli algoritmi al calice</h1>
      <p className="home-desc">
        Analizziamo profilo chimico, qualità e abbinamenti con modelli
        predittivi, per darti solo dati reali su ciò che troverai nel bicchiere.
      </p>

      <Link to="/catalogo" className="btn-primary home-cta">
        Inizia Qui
      </Link>

      {/* Le 2 metriche sono tenute distinte (0,52 e' la media in cross-validation,
          0,56 il test set indipendente: confonderle sarebbe scorretto). */}
      <ul className="trust-strip">
        <li>
          <span className="trust-value">6.497</span>
          <span className="trust-label">vini analizzati</span>
        </li>
        <li>
          <span className="trust-value">5-fold</span>
          <span className="trust-label">cross-validation · R² 0,52</span>
        </li>
        <li>
          <span className="trust-value">R² 0,56</span>
          <span className="trust-label">su test set indipendente</span>
        </li>
      </ul>
      <p className="trust-source">
        Dataset UCI Wine Quality · RandomForestRegressor con pipeline scikit-learn
      </p>
    </section>
  );
}
