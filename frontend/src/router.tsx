/**
 * Routing con TanStack Router, definito "a codice" (non file-based): ogni
 * rotta e' un oggetto esplicito, piu' facile da seguire riga per riga
 * quando si sta ancora imparando come funziona un router.
 */
import { createRootRoute, createRoute, createRouter, Outlet, Link } from "@tanstack/react-router";
import { Catalogo } from "./routes/Catalogo";
import { Predizione } from "./routes/Predizione";
import { Raccomandazioni } from "./routes/Raccomandazioni";
import { Sommelier } from "./routes/Sommelier";

const rootRoute = createRootRoute({
  component: () => (
    <div className="app">
      <header>
        <h1>🍷 WineScout Platform</h1>
        <p className="tagline">
          Trasformare l'istinto del sommelier in algoritmi predittivi grazie al Machine Learning
        </p>
        <nav>
          <Link to="/" activeProps={{ className: "active" }}>Catalogo Vini</Link>
          <Link to="/predizione" activeProps={{ className: "active" }}>Predizione Qualità</Link>
          <Link to="/raccomandazioni" activeProps={{ className: "active" }}>Raccomandazioni</Link>
          <Link to="/sommelier" activeProps={{ className: "active" }}>Sommelier Virtuale</Link>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  ),
});

const catalogoRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
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

const sommelierRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/sommelier",
  component: Sommelier,
});

const routeTree = rootRoute.addChildren([
  catalogoRoute,
  predizioneRoute,
  raccomandazioniRoute,
  sommelierRoute,
]);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
