"""Disegni SVG generati dai dati: bottiglia, radar chimico, figura di SVEVA.

Stessa logica dei componenti React (BottleIcon.tsx, ChemicalRadar.tsx,
RobotSommelierIcon.tsx), riscritta in Python per l'interfaccia Streamlit.
Sono funzioni pure che restituiscono una stringa SVG: si testano senza
avviare l'interfaccia.

Nessuna caratteristica inventata: tutto cio' che cambia nel disegno deriva
dal profilo reale del vino. L'etichetta resta muta perche' il dataset non
contiene denominazioni reali.
"""
import math

# Medie del dataset, usate quando il dato puntuale non e' disponibile.
ALCOL_MEDIO = 10.5
ZUCCHERO_MEDIO = 5.4

# Profilo bordolese: collo lungo e stretto, spalla raccordata, corpo dritto.
_SAGOMA = ("M24 14 L24 56 C24 72 10 76 10 92 L10 168 Q10 176 18 176 "
           "L42 176 Q50 176 50 168 L50 92 C50 76 36 72 36 56 L36 14 Z")


def _mescola(a: str, b: str, t: float) -> str:
    """Interpola fra due colori esadecimali (t da 0 a 1)."""
    t = max(0.0, min(1.0, t))
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def tavolozza(tipo: str, qualita: int, alcol: float | None) -> dict:
    """Colori della bottiglia dal profilo del vino.

    - tonalita' dal tipo (rubino/paglierino), intensita' dalla gradazione,
      il proxy disponibile piu' vicino alla struttura del vino;
    - veste piu' austera da qualita' 8 in su (colore piu' concentrato,
      capsula scura): il criterio e' il punteggio, un dato reale, non la
      menzione "Riserva" che il dataset non puo' giustificare;
    - capsula oro da qualita' 6, stagnola scura sotto.
    """
    rosso = tipo == "red"
    austera = qualita >= 8
    corpo = ((alcol if alcol is not None else ALCOL_MEDIO) - 8) / 7
    vino = _mescola("#a8394f", "#4a1220", corpo) if rosso else _mescola("#f7f0cd", "#e0be63", corpo)
    if austera:
        vino = _mescola(vino, "#2e0910" if rosso else "#b8863a", 0.35)
    return {
        "vino": vino,
        "chiaro": _mescola(vino, "#ffffff", 0.22 if rosso else 0.38),
        "scuro": _mescola(vino, "#000000", 0.4 if rosso else 0.24),
        "vetro": "#5b4038" if rosso else "#e9e6d4",
        "capsula": "#2a1017" if austera else ("#c9a24b" if qualita >= 6 else "#6b5a4a"),
        "austera": austera,
    }


def bottiglia(wine_id: int, tipo: str, qualita: int, alcol: float | None = None,
              zucchero: float | None = None, altezza: int = 150) -> str:
    """Bottiglia SVG: colore da tipo e gradazione, livello dallo zucchero,
    capsula dalla qualita'."""
    p = tavolozza(tipo, qualita, alcol)
    dolcezza = max(0.0, min(1.0, (zucchero if zucchero is not None else ZUCCHERO_MEDIO) / 20))
    livello = 60 - dolcezza * 26
    g, c = f"vino-{wine_id}", f"sagoma-{wine_id}"
    capsula = "M23 6 L37 6 L37 44 L23 44 Z" if p["austera"] else "M23 6 L37 6 L37 32 L23 32 Z"
    filetti = (
        f'<rect x="10" y="117" width="40" height="1.2" fill="rgba(169,132,56,.85)" clip-path="url(#{c})"/>'
        f'<rect x="10" y="152" width="40" height="1.2" fill="rgba(169,132,56,.85)" clip-path="url(#{c})"/>'
        if p["austera"] else ""
    )
    nome_tipo = "rosso" if tipo == "red" else "bianco"
    return (
        f'<svg viewBox="0 0 60 180" width="{round(altezza / 3)}" height="{altezza}" role="img" '
        f'aria-label="Bottiglia di vino {nome_tipo}">'
        f'<defs><linearGradient id="{g}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{p["scuro"]}"/><stop offset="30%" stop-color="{p["chiaro"]}"/>'
        f'<stop offset="62%" stop-color="{p["vino"]}"/><stop offset="100%" stop-color="{p["scuro"]}"/>'
        f'</linearGradient><clipPath id="{c}"><path d="{_SAGOMA}"/></clipPath></defs>'
        f'<path d="{_SAGOMA}" fill="url(#{g})"/>'
        f'<rect x="8" y="0" width="44" height="{livello:.1f}" fill="{p["vetro"]}" clip-path="url(#{c})"/>'
        f'<rect x="10" y="112" width="40" height="46" fill="rgba(247,244,232,.88)" clip-path="url(#{c})"/>'
        f'<rect x="10" y="146" width="40" height="4" fill="rgba(0,0,0,.07)" clip-path="url(#{c})"/>'
        f'{filetti}'
        f'<path d="{capsula}" fill="{p["capsula"]}" clip-path="url(#{c})"/>'
        f'<rect x="23" y="{40 if p["austera"] else 28}" width="14" height="2.5" fill="rgba(0,0,0,.28)"/>'
        f'<rect x="15" y="66" width="3" height="42" rx="1.5" fill="rgba(255,255,255,.3)"/>'
        f'<rect x="27.5" y="16" width="2" height="34" rx="1" fill="rgba(255,255,255,.22)"/>'
        f'<path d="{_SAGOMA}" fill="none" stroke="rgba(0,0,0,.28)" stroke-width="1"/>'
        f'</svg>'
    )


# Range tipici del dataset UCI: ogni asse va da 0 a 100%, cosi' grandezze con
# unita' diverse (pH e g/L di cloruri) stanno sullo stesso grafico.
ASSI_RADAR = [
    ("Alcol", "alcohol", 8, 15),
    ("pH", "ph", 2.7, 4.0),
    ("Acidità fissa", "fixed_acidity", 4, 16),
    ("Acidità volatile", "volatile_acidity", 0.1, 1.6),
    ("Cloruri", "chlorides", 0.01, 0.6),
    ("Solfati", "sulphates", 0.3, 2.0),
]


def valori_radar(vino: dict) -> list[float]:
    """Valori normalizzati 0-100 per gli assi del radar."""
    return [max(0.0, min(100.0, (float(vino[c]) - lo) / (hi - lo) * 100))
            for _, c, lo, hi in ASSI_RADAR]


def radar(vino: dict, lato: int = 300) -> str:
    """Radar SVG del profilo chimico normalizzato."""
    cx = cy = lato / 2
    r = lato * 0.32
    n = len(ASSI_RADAR)

    def punto(i: int, frazione: float) -> tuple[float, float]:
        angolo = -math.pi / 2 + 2 * math.pi * i / n
        return cx + r * frazione * math.cos(angolo), cy + r * frazione * math.sin(angolo)

    griglia = "".join(
        f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in (punto(i, f) for i in range(n)))}" '
        f'fill="none" stroke="rgba(244,236,226,.22)" stroke-width="1"/>'
        for f in (0.25, 0.5, 0.75, 1.0)
    )
    raggi = "".join(
        f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="rgba(244,236,226,.14)"/>'
        for x, y in (punto(i, 1.0) for i in range(n))
    )
    valori = valori_radar(vino)
    forma = " ".join(f"{x:.1f},{y:.1f}" for x, y in (punto(i, v / 100) for i, v in enumerate(valori)))
    etichette = ""
    for i, (nome, *_rest) in enumerate(ASSI_RADAR):
        x, y = punto(i, 1.22)
        ancora = "middle" if abs(x - cx) < 5 else ("start" if x > cx else "end")
        etichette += (f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="{ancora}" '
                      f'font-size="12" font-family="Inter, Segoe UI, sans-serif" '
                      f'fill="#e7d3a3">{nome}</text>')
    # Margine laterale di 80 unita': le etichette dei vertici destro e
    # sinistro ("Acidità fissa", "Cloruri") escono dal quadrato del grafico.
    margine = 80
    return (
        f'<svg viewBox="{-margine} 0 {lato + 2 * margine} {lato}" width="100%" '
        f'style="max-width:{lato + 2 * margine}px" role="img" '
        f'aria-label="Profilo chimico normalizzato">{griglia}{raggi}'
        f'<polygon points="{forma}" fill="rgba(231,211,163,.28)" stroke="#e7d3a3" stroke-width="2"/>'
        f'{etichette}</svg>'
    )


def sveva_figura(larghezza: int = 130) -> str:
    """Figura intera di SVEVA (stessa di RobotSommelierIcon.tsx)."""
    return (
        f'<svg viewBox="0 0 200 220" width="{larghezza}" height="{round(larghezza * 1.1)}" aria-hidden="true">'
        '<ellipse cx="100" cy="55" rx="46" ry="38" fill="#2a1015" stroke="#c9a24b" stroke-width="4"/>'
        '<ellipse cx="108" cy="55" rx="20" ry="16" fill="#f3e6cf"/>'
        '<circle cx="72" cy="45" r="4" fill="#c9a24b"/><circle cx="72" cy="58" r="4" fill="#e8d98a"/>'
        '<circle cx="72" cy="71" r="4" fill="#6d1b2f"/>'
        '<path d="M60 95 L140 95 L150 200 Q150 212 138 212 L62 212 Q50 212 50 200 Z" fill="#4a1220"/>'
        '<path d="M85 95 L100 130 L115 95 Z" fill="#f3e6cf"/>'
        '<rect x="92" y="140" width="16" height="20" rx="2" fill="#c9a24b"/>'
        '<rect x="132" y="105" width="14" height="55" rx="6" fill="#f3e6cf" transform="rotate(18 132 105)"/>'
        '<rect x="150" y="150" width="45" height="8" rx="3" fill="#2a1015"/>'
        '<rect x="163" y="118" width="10" height="30" rx="2" fill="#3f5c3f"/>'
        '<rect x="166" y="112" width="4" height="8" fill="#3f5c3f"/>'
        '<path d="M186 130 Q186 142 178 142 Q170 142 170 130 L170 124 L186 124 Z" fill="#e8d98a"/>'
        '<rect x="177" y="142" width="2.5" height="10" fill="#ccc"/>'
        '<rect x="88" y="205" width="24" height="12" rx="4" fill="#2a1015"/>'
        '</svg>'
    )
