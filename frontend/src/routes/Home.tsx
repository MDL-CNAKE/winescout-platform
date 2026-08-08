/**
 * Homepage: hero compatto e catalogo in griglia.
 *
 * Chi arriva vede subito l'offerta invece di una pagina di presentazione:
 * il claim resta, ridotto a due righe, e sotto partono filtri e referenze.
 *
 * Filtri, ordinamento e paginazione sono parametri dell'API, non lavoro del
 * browser: con 6497 record scaricarli tutti per mostrarne 24 sarebbe uno
 * spreco, e ogni cambio di filtro rifa' la query lato server.
 */
import { useEffect, useState } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { searchWines, fetchWineFacets, type SortOption } from "../api";
import { FilterBar, EMPTY_FILTERS, type Filters } from "../components/FilterBar";
import { WineGridCard } from "../components/WineGridCard";
import { Pagination } from "../components/Pagination";
import { EmptyState } from "../components/EmptyState";
import { useFavorites } from "../hooks/useFavorites";

const PAGE_SIZE = 24;

export function Home() {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [sort, setSort] = useState<SortOption>("quality_desc");
  const [page, setPage] = useState(1);
  const { isFavorite, toggle, othersFor } = useFavorites();

  // Cambiare filtri o ordinamento invalida la pagina corrente: restare
  // alla 12 dopo aver ristretto a 30 risultati mostrerebbe il vuoto.
  useEffect(() => setPage(1), [filters, sort]);

  const { data: facets } = useQuery({ queryKey: ["facets"], queryFn: fetchWineFacets });

  const { data, isLoading, isError } = useQuery({
    queryKey: ["search", filters, sort, page],
    queryFn: () => searchWines({ ...filters, sort, page, page_size: PAGE_SIZE }),
    // Tiene a schermo la pagina precedente durante il caricamento della
    // successiva, evitando che la griglia sparisca a ogni click.
    placeholderData: keepPreviousData,
  });

  return (
    <section className="home">

      <FilterBar
        filters={filters}
        onFiltersChange={setFilters}
        sort={sort}
        onSortChange={setSort}
        total={data?.total}
        facets={facets}
      />

      {isError && (
        <EmptyState
          title="Non riesco a raggiungere il catalogo."
          hint="Verifica che il servizio sia attivo e riprova."
        />
      )}

      {!isError && isLoading && !data && (
        <EmptyState title="Il sommelier sta preparando il catalogo..." loading />
      )}

      {data && data.items.length === 0 && (
        <EmptyState
          title="Nessuna referenza con questi criteri."
          hint="Prova ad allargare gli intervalli o ad azzerare i filtri."
        />
      )}

      {data && data.items.length > 0 && (
        <>
          <div className="wine-grid">
            {data.items.map((w) => (
              <WineGridCard
                key={w.id}
                wine={w}
                isFavorite={isFavorite(w.id)}
                onToggleFavorite={toggle}
                others={othersFor(w.id)}
              />
            ))}
          </div>

          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onPageChange={(p) => {
              setPage(p);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          />
        </>
      )}

      {/* Credenziali del modello in chiusura: le due metriche restano
          distinte, 0,52 e' la media in cross-validation e 0,56 il test set
          indipendente. Confonderle sarebbe scorretto. */}
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
