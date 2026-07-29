/**
 * Contenitore scorrevole orizzontalmente, con due frecce per scorrere
 * di una "pagina" di card alla volta invece che a scatti di pixel.
 */
import { useRef, type ReactNode } from "react";

export function Carousel({ children }: { children: ReactNode }) {
  const trackRef = useRef<HTMLDivElement>(null);

  const scroll = (dir: 1 | -1) => {
    const el = trackRef.current;
    if (!el) return;
    el.scrollBy({ left: dir * el.clientWidth * 0.8, behavior: "smooth" });
  };

  return (
    <div className="carousel">
      <button className="carousel-arrow left" onClick={() => scroll(-1)} aria-label="Precedente">
        ‹
      </button>
      <div className="carousel-track" ref={trackRef}>
        {children}
      </div>
      <button className="carousel-arrow right" onClick={() => scroll(1)} aria-label="Successivo">
        ›
      </button>
    </div>
  );
}
