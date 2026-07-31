/**
 * Paginazione numerata.
 *
 * Con 6497 referenze le pagine sono centinaia: si mostrano solo quelle
 * vicine a quella corrente, piu' la prima e l'ultima, separate da puntini.
 */
interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

function pagesToShow(current: number, last: number): (number | "gap")[] {
  if (last <= 7) return Array.from({ length: last }, (_, i) => i + 1);

  const around = [current - 1, current, current + 1].filter((p) => p > 1 && p < last);
  const out: (number | "gap")[] = [1];
  if (around[0] > 2) out.push("gap");
  out.push(...around);
  if (around[around.length - 1] < last - 1) out.push("gap");
  out.push(last);
  return out;
}

export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const last = Math.max(1, Math.ceil(total / pageSize));
  if (last <= 1) return null;

  return (
    <nav className="pagination" aria-label="Pagine del catalogo">
      <button
        type="button"
        className="page-btn"
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        aria-label="Pagina precedente"
      >
        ‹
      </button>

      {pagesToShow(page, last).map((p, i) =>
        p === "gap" ? (
          <span key={`gap-${i}`} className="page-gap">
            …
          </span>
        ) : (
          <button
            key={p}
            type="button"
            className={`page-btn${p === page ? " active" : ""}`}
            onClick={() => onPageChange(p)}
            aria-current={p === page ? "page" : undefined}
          >
            {p}
          </button>
        )
      )}

      <button
        type="button"
        className="page-btn"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= last}
        aria-label="Pagina successiva"
      >
        ›
      </button>
    </nav>
  );
}
