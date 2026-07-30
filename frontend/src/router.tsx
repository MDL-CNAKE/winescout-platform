/**
 * Routing con TanStack Router, definito "a codice" (non file-based): ogni
 * rotta e' un oggetto esplicito, piu' facile da seguire riga per riga
 * quando si sta ancora imparando come funziona un router.
 */
import { createRootRoute, createRoute, createRouter, Outlet, Link } from "@tanstack/react-router";
import { Home } from "./routes/Home";
import { Catalogo } from "./routes/Catalogo";
import { Predizione } from "./routes/Predizione";
import { Raccomandazioni } from "./routes/Raccomandazioni";
import { Packaging } from "./routes/Packaging";
import { Sommelier } from "./routes/Sommelier";
import { Vino } from "./routes/Vino";

const rootRoute = createRootRoute({
  component: () => (
    <div className="app">
      <header>
        <Link to="/" className="brand-mark">
          <span className="brand-mark-name">Bacchus</span>
          <span className="brand-mark-sub">WineScout AI</span>
        </Link>
        <nav>
          <Link to="/" activeProps={{ className: "active" }}>Home</Link>
          <Link to="/catalogo" activeProps={{ className: "active" }}>Catalogo Vini</Link>
          <Link to="/sommelier" activeProps={{ className: "active" }}>Sommelier Virtuale</Link>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="site-footer">
        <p>
          Dati elaborati tramite API e modello predittivo su dataset enologico reale.
          Prezzi e margini sono simulati con una logica di business, non listini commerciali;
          descrizioni e abbinamenti derivano dai dati chimici, non da testo redazionale.
        </p>
      </footer>
    </div>
  ),
});

const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: Home,
});

const catalogoRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/catalogo",
  component: Catalogo,
});

const predizioneRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/predizione",
  component: Predizione,
});

const raccomandazioniRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/raccomandazioni",
  component: Raccomandazioni,
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
  catalogoRoute,
  predizioneRoute,
  raccomandazioniRoute,
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
