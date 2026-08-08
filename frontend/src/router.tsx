/**
 * Routing con TanStack Router, definito "a codice" (non file-based): ogni
 * rotta e' un oggetto esplicito, piu' facile da seguire riga per riga
 * quando si sta ancora imparando come funziona un router.
 */
import { createRootRoute, createRoute, createRouter, Outlet, Link } from "@tanstack/react-router";
import { Home } from "./routes/Home";
import { Predizione } from "./routes/Predizione";
import { Packaging } from "./routes/Packaging";
import { Conservazione } from "./routes/Conservazione";
import { Sommelier } from "./routes/Sommelier";
import { Vino } from "./routes/Vino";
import { Vendite } from "./routes/Vendite";
import { Spedizioni } from "./routes/Spedizioni";
import { BrandLockup } from "./components/BrandLockup";
import { PoweredBy } from "./components/PoweredBy";
import { OperatorPicker } from "./components/OperatorPicker";
import { useFavorites } from "./hooks/useFavorites";
import type { Ruolo } from "./api";

/**
 * Sezioni mostrate a ciascun ruolo.
 *
 * Non e' un sistema di permessi: l'applicazione appartiene a una sola
 * cantina e chiunque puo' cambiare operatore. Serve a mettere in evidenza
 * gli strumenti del proprio mestiere invece di tutti insieme — le altre
 * sezioni restano raggiungibili via URL.
 */
const SEZIONI = [
  { to: "/", label: "Catalogo" },
  { to: "/vendite", label: "Vendite" },
  { to: "/predizione", label: "Predizione" },
  { to: "/conservazione", label: "Conservazione" },
  { to: "/packaging", label: "Packaging" },
  { to: "/spedizioni", label: "Spedizioni" },
  { to: "/sommelier", label: "SVEVA" },
] as const;

const PER_RUOLO: Record<Ruolo, string[]> = {
  // Il titolare guarda l'insieme: nessun filtro.
  titolare: SEZIONI.map((s) => s.to),
  // L'enologo lavora sulla chimica del vino e sulla tenuta dei lotti.
  enologo: ["/", "/predizione", "/conservazione", "/sommelier"],
  // Chi vende lavora su canali, margini e presentazione del prodotto.
  vendite: ["/", "/vendite", "/packaging", "/sommelier"],
  // La logistica guarda cosa c'e', come e' confezionato e cosa deve partire.
  logistica: ["/", "/packaging", "/spedizioni"],
};

function Layout() {
  const { operators, operatorId } = useFavorites();
  const ruolo = operators?.find((o) => o.id === operatorId)?.role ?? "titolare";
  const visibili = SEZIONI.filter((s) => PER_RUOLO[ruolo].includes(s.to));

  return (
    <div className="app">
      <header>
        <Link to="/" className="brand-mark" aria-label="CruScout — torna alla home">
          <BrandLockup variant="header" />
          <span className="brand-mark-sub">Il cruscotto del piccolo produttore</span>
        </Link>

        <nav>
          {visibili.map((s) => (
            <Link key={s.to} to={s.to} activeProps={{ className: "active" }}>
              {s.label}
            </Link>
          ))}
        </nav>

        {/* Il ruolo governa la navigazione: si cambia da qualunque pagina. */}
        <OperatorPicker />
      </header>

      <main>
        <Outlet />
      </main>
      <PoweredBy />
      <footer className="site-footer">
        <p>
          Dati elaborati tramite API e modello predittivo su dataset enologico reale.
          Prezzi e margini sono simulati con una logica di business, non listini commerciali;
          descrizioni e abbinamenti derivano dai dati chimici, non da testo redazionale.
        </p>
      </footer>
    </div>
  );
}

const rootRoute = createRootRoute({ component: Layout });

const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: Home,
});

const predizioneRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/predizione",
  component: Predizione,
});

const conservazioneRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/conservazione",
  component: Conservazione,
});

const venditeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/vendite",
  component: Vendite,
});

const spedizioniRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/spedizioni",
  component: Spedizioni,
});

const packagingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/packaging",
  component: Packaging,
});

const vinoRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/vino/$wineId",
  component: Vino,
});

const sommelierRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/sommelier",
  component: Sommelier,
});

const routeTree = rootRoute.addChildren([
  homeRoute,
  predizioneRoute,
  conservazioneRoute,
  venditeRoute,
  spedizioniRoute,
  packagingRoute,
  vinoRoute,
  sommelierRoute,
]);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
