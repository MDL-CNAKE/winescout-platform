"""Predisposizione alla conservazione di un vino, da parametri enologici reali.

PERCHE' "CONSERVAZIONE" E NON "INVECCHIAMENTO"
----------------------------------------------
Il potenziale di invecchiamento nobile - l'evoluzione verso i profumi
terziari, l'ammorbidimento della struttura - dipende in larga parte da
tannini, polifenoli ed estratto secco, che nel dataset UCI NON ci sono. Per
un rosso, in particolare, il tannino e' la struttura portante
dell'invecchiamento: senza quel dato qualunque previsione sull'evoluzione
sarebbe inventata.

Cio' che i dati permettono di valutare e' un'altra cosa, piu' ristretta ma
concreta: la capacita' del vino di resistere a ossidazione e alterazione
microbica, cioe' se regge la conservazione o va immesso sul mercato subito.
E' la domanda commerciale che una piccola cantina si pone davvero.

NON E' UN MODELLO ADDESTRATO
-----------------------------
Il dataset non contiene alcuna etichetta sull'evoluzione dei vini nel tempo:
non esiste una verita' di riferimento su cui addestrare o validare un
modello. Questo indice e' quindi un sistema A REGOLE costruito su parametri
enologici consolidati, come src/pairing.py, e va presentato come tale: non
ha un'accuratezza misurabile, ha una motivazione ispezionabile riga per riga.

I QUATTRO INDICATORI
--------------------
1. SO2 MOLECOLARE - la frazione di anidride solforosa realmente attiva.
   La SO2 libera totale dice poco da sola: la sua efficacia dipende dal pH,
   perche' solo la forma molecolare indissociata agisce contro lieviti e
   batteri. Formula standard: SO2mol = SO2_libera / (1 + 10^(pH - pKa)),
   con pKa = 1,81. Riferimento operativo diffuso: 0,5-0,8 mg/L.

2. QUOTA DI SO2 LIBERA sul totale - quanta solforosa e' ancora disponibile
   invece che legata (ad acetaldeide, zuccheri, antociani). Una quota bassa
   indica una riserva gia' consumata.

3. ACIDITA' VOLATILE - marcatore di deterioramento in atto (acido acetico,
   spunto). I limiti di legge UE sono 1,2 g/L per i rossi e 1,08 g/L per i
   bianchi: avvicinarvisi significa che il vino ha gia' un problema, non che
   lo avra'.

4. pH - agisce due volte: e' esso stesso un conservante (i vini piu' acidi
   resistono meglio) e governa l'efficacia della solforosa, motivo per cui
   l'indicatore 1 dipende da lui.

LIMITI DA DICHIARARE
--------------------
- Il dataset e' composto da Vinho Verde portoghesi, vini pensati per il
  consumo giovane: una solforosa contenuta e' in parte fisiologica e non
  necessariamente un errore di cantina.
- Mancano tannini, polifenoli, estratto secco, annata e condizioni di
  conservazione: l'indice parla di stabilita' chimica, non di destino
  organolettico.
"""
from dataclasses import dataclass

# Costante di dissociazione dell'anidride solforosa.
PKA_SO2 = 1.81

# Riferimenti operativi per la SO2 molecolare (mg/L).
SO2_MOL_INSUFFICIENTE = 0.5
SO2_MOL_OTTIMALE = 0.8

# Limiti di legge per l'acidita' volatile (g/L di acido acetico), Reg. UE.
VA_LIMITE = {"red": 1.2, "white": 1.08}


@dataclass
class Indicatore:
    """Un singolo parametro, con il suo valore e come va letto."""
    nome: str
    valore: float
    unita: str
    livello: str          # "buono" | "attenzione" | "critico"
    spiegazione: str


@dataclass
class Conservazione:
    punteggio: int                    # 0-100, per ordinare il catalogo
    giudizio: str                     # sintesi in una parola
    indicatori: list[Indicatore]


def so2_molecolare(free_so2: float, ph: float) -> float:
    """Frazione di SO2 realmente attiva, in mg/L."""
    return free_so2 / (1 + 10 ** (ph - PKA_SO2))


def _valuta_so2_molecolare(value: float) -> tuple[str, float, str]:
    if value >= SO2_MOL_OTTIMALE:
        return "buono", 1.0, (
            "Protezione antiossidante e antimicrobica piena: il vino regge "
            "la conservazione senza interventi."
        )
    if value >= SO2_MOL_INSUFFICIENTE:
        return "attenzione", 0.6, (
            "Protezione al limite inferiore. Sufficiente nel breve periodo, "
            "da monitorare se il lotto resta in cantina a lungo."
        )
    return "critico", 0.15, (
        "Protezione sotto la soglia operativa: il vino e' esposto a "
        "ossidazione e rifermentazione. Da immettere sul mercato in tempi "
        "brevi, oppure da correggere prima dello stoccaggio."
    )


def _valuta_quota_libera(value: float) -> tuple[str, float, str]:
    if value >= 0.35:
        return "buono", 1.0, (
            "Buona parte della solforosa e' ancora libera: la riserva "
            "protettiva non e' stata consumata."
        )
    if value >= 0.20:
        return "attenzione", 0.6, (
            "Quota libera moderata: una parte della solforosa risulta gia' "
            "legata e non piu' disponibile."
        )
    return "critico", 0.2, (
        "Solforosa in gran parte legata: la riserva utile e' quasi esaurita, "
        "anche se il valore totale sembra alto."
    )


def _valuta_acidita_volatile(value: float, wine_type: str) -> tuple[str, float, str]:
    limite = VA_LIMITE.get(wine_type, 1.2)
    rapporto = value / limite
    if rapporto <= 0.5:
        return "buono", 1.0, (
            f"Acidita' volatile contenuta ({value:.2f} g/L, limite di legge "
            f"{limite} g/L): nessun segnale di alterazione."
        )
    if rapporto <= 0.8:
        return "attenzione", 0.5, (
            f"Acidita' volatile elevata ({value:.2f} g/L su un limite di "
            f"{limite} g/L): indica un processo di deterioramento gia' avviato."
        )
    return "critico", 0.0, (
        f"Acidita' volatile prossima o oltre il limite di legge "
        f"({value:.2f} contro {limite} g/L): il vino presenta un difetto "
        f"conclamato, la conservazione lo aggraverebbe."
    )


def _valuta_ph(value: float) -> tuple[str, float, str]:
    if value <= 3.3:
        return "buono", 1.0, (
            "pH basso: l'acidita' agisce da conservante e rende la solforosa "
            "piu' efficace a parita' di dose."
        )
    if value <= 3.6:
        return "attenzione", 0.6, (
            "pH intermedio: conservazione possibile, ma la solforosa perde "
            "efficacia man mano che il pH sale."
        )
    return "critico", 0.2, (
        "pH elevato: scarso effetto conservante dell'acidita' e solforosa "
        "poco efficace. Vino da consumare giovane."
    )


# Pesi degli indicatori nel punteggio composito. La SO2 molecolare pesa piu'
# degli altri perche' e' l'unico parametro su cui la cantina puo' intervenire
# direttamente; l'acidita' volatile ha peso alto perche' un suo valore
# critico e' un difetto conclamato, non un rischio.
PESI = {
    "so2_molecolare": 0.40,
    "acidita_volatile": 0.30,
    "ph": 0.20,
    "quota_libera": 0.10,
}


def valuta_conservazione(
    *,
    wine_type: str,
    free_sulfur_dioxide: float,
    total_sulfur_dioxide: float,
    ph: float,
    volatile_acidity: float,
) -> Conservazione:
    """Calcola indicatori e punteggio sintetico di conservazione."""
    so2_mol = so2_molecolare(free_sulfur_dioxide, ph)
    quota = (
        free_sulfur_dioxide / total_sulfur_dioxide
        if total_sulfur_dioxide > 0
        else 0.0
    )

    liv_so2, p_so2, sp_so2 = _valuta_so2_molecolare(so2_mol)
    liv_quota, p_quota, sp_quota = _valuta_quota_libera(quota)
    liv_va, p_va, sp_va = _valuta_acidita_volatile(volatile_acidity, wine_type)
    liv_ph, p_ph, sp_ph = _valuta_ph(ph)

    punteggio = round(
        100
        * (
            p_so2 * PESI["so2_molecolare"]
            + p_va * PESI["acidita_volatile"]
            + p_ph * PESI["ph"]
            + p_quota * PESI["quota_libera"]
        )
    )

    if punteggio >= 75:
        giudizio = "Adatto alla conservazione"
    elif punteggio >= 45:
        giudizio = "Conservazione con monitoraggio"
    else:
        giudizio = "Da immettere sul mercato"

    return Conservazione(
        punteggio=punteggio,
        giudizio=giudizio,
        indicatori=[
            Indicatore("SO2 molecolare", round(so2_mol, 3), "mg/L", liv_so2, sp_so2),
            Indicatore("Acidita volatile", round(volatile_acidity, 2), "g/L", liv_va, sp_va),
            Indicatore("pH", round(ph, 2), "", liv_ph, sp_ph),
            Indicatore("Quota SO2 libera", round(quota * 100), "%", liv_quota, sp_quota),
        ],
    )
