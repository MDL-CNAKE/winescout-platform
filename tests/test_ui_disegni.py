"""Test dei disegni SVG generati dai dati (src/ui/disegni.py)."""
import xml.etree.ElementTree as ET

from src.ui.disegni import bottiglia, radar, sveva_figura, tavolozza, valori_radar

VINO = {"id": 7, "type": "red", "quality": 6, "alcohol": 11.5, "ph": 3.35,
        "fixed_acidity": 7.4, "volatile_acidity": 0.5, "chlorides": 0.08, "sulphates": 0.6,
        "residual_sugar": 2.0}


def test_gli_svg_sono_xml_valido():
    # Un attributo malformato romperebbe il disegno senza errori visibili.
    for svg in (bottiglia(7, "red", 6, 11.5, 2.0), bottiglia(8, "white", 8),
                radar(VINO), sveva_figura()):
        ET.fromstring(svg)


def test_identificativi_unici_per_vino():
    # Gradiente e sagoma sono referenziati per id: due card con lo stesso id
    # mostrerebbero tutte il colore della prima.
    assert 'id="vino-7"' in bottiglia(7, "red", 6)
    assert 'id="vino-8"' in bottiglia(8, "red", 6)


def test_capsula_dalla_qualita():
    assert tavolozza("red", 5, 11)["capsula"] == "#6b5a4a"
    assert tavolozza("red", 6, 11)["capsula"] == "#c9a24b"
    assert tavolozza("red", 8, 11)["capsula"] == "#2a1017"
    assert tavolozza("red", 8, 11)["austera"] is True


def test_rosso_e_bianco_hanno_colori_diversi():
    assert tavolozza("red", 6, 11)["vino"] != tavolozza("white", 6, 11)["vino"]


def test_piu_dolce_piu_colma():
    # Lo zucchero residuo riduce lo spazio d'aria sotto la capsula.
    def altezza_aria(svg: str) -> float:
        return float(svg.split('<rect x="8" y="0" width="44" height="')[1].split('"')[0])

    assert altezza_aria(bottiglia(1, "white", 6, 11, 30)) < altezza_aria(bottiglia(1, "white", 6, 11, 1))


def test_radar_normalizzato_e_limitato():
    valori = valori_radar({**VINO, "alcohol": 20, "ph": 2.0})
    assert valori[0] == 100.0  # oltre il massimo del range
    assert valori[1] == 0.0    # sotto il minimo del range
    assert all(0 <= v <= 100 for v in valori)
