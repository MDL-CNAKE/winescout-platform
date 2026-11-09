"""Formattazione dei dati per l'interfaccia, senza dipendenze da Streamlit.

E' logica pura: sta in un modulo separato dalle pagine per poterla testare
senza avviare l'interfaccia (vedi tests/test_ui_formato.py).
"""
import re

# I nomi in database hanno la forma "Rosso Corposo Armonico - Lotto #0042"
# (vedi src/naming.py). Il lotto distingue referenze con chimica simile, ma
# nelle tabelle conviene mostrarlo in una colonna sua.
_LOTTO_RE = re.compile(r"\s*-\s*Lotto\s*#(\d+)\s*$", re.IGNORECASE)


def titolo_vino(nome: str) -> str:
    """Nome senza il suffisso del lotto: "Rosso Corposo Armonico"."""
    return _LOTTO_RE.sub("", nome or "").strip()


def lotto_vino(nome: str) -> str | None:
    """Solo il codice di lotto, se presente: "#0042"."""
    trovato = _LOTTO_RE.search(nome or "")
    return f"#{trovato.group(1)}" if trovato else None


def tipo_esteso(tipo: str | None) -> str:
    """"red"/"white" del database in italiano."""
    return {"red": "Rosso", "white": "Bianco"}.get(tipo or "", "—")


def euro(valore: float | None) -> str:
    """Importo con la virgola decimale italiana: "12,34 €"."""
    if valore is None:
        return "—"
    return f"{float(valore):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def livello_conservazione(punteggio: int) -> str:
    """Stesse soglie di src/conservation.py: il livello non si ricalcola qui
    con regole diverse, si legge dal punteggio che il backend ha prodotto."""
    if punteggio >= 75:
        return "buono"
    if punteggio >= 45:
        return "attenzione"
    return "critico"


def abbinamenti(food_pairing: str | None) -> list[str]:
    """La stringa di abbinamento divisa nei singoli piatti."""
    if not food_pairing:
        return []
    return [p.strip() for p in food_pairing.split(",") if p.strip()]


def corpo(alcol: float) -> str:
    """Stesse soglie di frontend/src/lib/wineLabel.ts."""
    if alcol >= 12.0:
        return "corposo"
    if alcol <= 9.5:
        return "leggero"
    return "equilibrato"


def dolcezza(zucchero: float, acidita: float) -> str:
    """Dolcezza secondo il Reg. UE 2019/33, con la correzione per l'acidita':
    a parita' di zucchero un vino piu' acido e' percepito piu' secco. Stesse
    soglie di src/wine_style.py."""
    if zucchero <= 4 or (zucchero <= 9 and acidita >= zucchero - 2):
        return "secco"
    if zucchero <= 12 or (zucchero <= 18 and acidita >= zucchero - 10):
        return "abboccato"
    if zucchero <= 45:
        return "amabile"
    return "dolce"


def abbinamento_principale(vino: dict) -> str | None:
    """Un piatto della lista, a rotazione sull'id del vino.

    Le regole di src/pairing.py classificano i 6.497 vini in sette fasce: senza
    rotazione le card vicine ripeterebbero lo stesso piatto. E' una
    mitigazione di presentazione, non cambia la granularita' delle regole.
    """
    piatti = [p.split("(")[0].strip() for p in abbinamenti(vino.get("food_pairing"))]
    piatti = [p for p in piatti if p]
    return piatti[vino["id"] % len(piatti)] if piatti else None


def descrizione_card(vino: dict) -> str:
    """Descrizione costruita dai valori chimici, non testo redazionale."""
    tipo = "rosso" if vino["type"] == "red" else "bianco"
    base = (f"Un {tipo} {corpo(vino['alcohol'])}, "
            f"{dolcezza(vino['residual_sugar'], vino['fixed_acidity'])}, "
            f"{vino['alcohol']:.1f}% vol con pH {vino['ph']:.2f}.")
    piatto = abbinamento_principale(vino)
    if not piatto:
        return base
    preposizione = "come" if piatto.lower() == "aperitivo" else "con"
    return f"{base} Da provare {preposizione} {piatto.lower()}."


def iniziali(nome: str) -> str:
    return "".join(p[0].upper() for p in nome.split()[:2] if p)


def descrivi_criteri(profilo: dict) -> str:
    """Riassume i vincoli di un profilo di mercato in una riga leggibile."""
    parti: list[str] = []
    if profilo.get("wine_type"):
        parti.append("rossi" if profilo["wine_type"] == "red" else "bianchi")
    if profilo.get("min_quality") is not None:
        parti.append(f"qualità ≥ {profilo['min_quality']}")
    if profilo.get("min_alcohol") is not None:
        parti.append(f"alcol ≥ {profilo['min_alcohol']}%")
    if profilo.get("max_alcohol") is not None:
        parti.append(f"alcol ≤ {profilo['max_alcohol']}%")
    if profilo.get("max_sugar") is not None:
        parti.append(f"zucchero ≤ {profilo['max_sugar']} g/L")
    if profilo.get("min_acidity") is not None:
        parti.append(f"acidità ≥ {profilo['min_acidity']} g/L")
    if profilo.get("max_price") is not None:
        parti.append(f"prezzo ≤ {profilo['max_price']} €")
    return " · ".join(parti) if parti else "nessun vincolo: tutto il catalogo"


def descrivi_metriche(metriche: dict | None) -> str:
    """Tempi, token e modello di una risposta LLM in una riga.

    I due tempi restano separati: se domina il recupero si lavora sull'indice,
    se domina la generazione su modello o lunghezza della risposta.
    """
    if not metriche:
        return ""
    parti: list[str] = []
    if metriche.get("ms_recupero") is not None:
        parti.append(f"recupero {metriche['ms_recupero']} ms")
    if metriche.get("ms_generazione") is not None:
        parti.append(f"generazione {metriche['ms_generazione']} ms")
    if metriche.get("token_prompt") is not None and metriche.get("token_risposta") is not None:
        parti.append(f"token {metriche['token_prompt']} + {metriche['token_risposta']}")
    if metriche.get("modello"):
        parti.append(metriche["modello"])
    return " · ".join(parti)
