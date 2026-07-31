/**
 * Routing con TanStack Router, definito "a codice" (non file-based): ogni
 * rotta e' un oggetto esplicito, piu' facile da seguire riga per riga
 * quando si sta ancora imparando come funziona un router.
 */
import { createRootRoute, createRoute, createRouter, Outlet, Link } from "@tanstack/react-router";
import { Home } from "./routes/Home";
import { Predizione } from "./routes/Predizione";
import { Packaging } from "./routes/Packaging";
import { Sommelier } from "./routes/Sommelier";
import { Vino } from "./routes/Vino";
import { BrandLockup } from "./components/BrandLockup";
import { PoweredBy } from "./components/PoweredBy";

const rootRoute = createRootRoute({
  component: () => (
    <div className="app">
      <header>
        <Link to="/" className="brand-mark" aria-label="CruScout — torna alla home">
          <BrandLockup variant="header" />
          <span className="brand-mark-sub">Il cruscotto del piccolo produttore</span>
        </Link>

        <nav>
          <Link to="/" activeProps={{ className: "active" }}>Catalogo</Link>
          <Link to="/predizione" activeProps={{ className: "active" }}>Predizione</Link>
          <Link to="/packaging" activeProps={{ className: "active" }}>Packaging</Link>
          <Link to="/sommelier" activeProps={{ className: "active" }}>Sommelier Virtuale</Link>
        </nav>
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
  ),
});

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
