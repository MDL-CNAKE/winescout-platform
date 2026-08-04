"""Test per src/conservation.py: indice di predisposizione alla conservazione."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.conservation import so2_molecolare, valuta_conservazione


def test_so2_molecolare_dipende_dal_ph():
    """A parita' di solforosa libera, un pH piu' alto lascia meno SO2 attiva:
    e' il motivo per cui il solo valore di SO2 libera non basta."""
    bassa_acidita = so2_molecolare(free_so2=30, ph=3.6)
    alta_acidita = so2_molecolare(free_so2=30, ph=3.0)
    assert alta_acidita > bassa_acidita
    # Con pH 3.0 e 30 mg/L liberi si superano gli 0.5 mg/L di riferimento;
    # con pH 3.6, a parita' di dose, no.
    assert alta_acidita > 0.5
    assert bassa_acidita < 0.5


def test_vino_ben_protetto():
    c = valuta_conservazione(
        wine_type="white", free_sulfur_dioxide=45, total_sulfur_dioxide=120,
        ph=3.05, volatile_acidity=0.22,
    )
    assert c.punteggio >= 75
    assert c.giudizio == "Adatto alla conservazione"


def test_vino_da_immettere_sul_mercato():
    """Poca solforosa attiva, pH alto e acidita' volatile elevata."""
    c = valuta_conservazione(
        wine_type="red", free_sulfur_dioxide=5, total_sulfur_dioxide=60,
        ph=3.75, volatile_acidity=1.0,
    )
    assert c.punteggio < 45
    assert c.giudizio == "Da immettere sul mercato"


def test_acidita_volatile_oltre_limite_azzera_il_contributo():
    """Oltre il limite di legge il difetto e' conclamato: quell'indicatore
    non deve contribuire al punteggio, per quanto il resto sia in ordine."""
    sano = valuta_conservazione(
        wine_type="red", free_sulfur_dioxide=40, total_sulfur_dioxide=100,
        ph=3.1, volatile_acidity=0.3,
    )
    difettoso = valuta_conservazione(
        wine_type="red", free_sulfur_dioxide=40, total_sulfur_dioxide=100,
        ph=3.1, volatile_acidity=1.3,
    )
    assert difettoso.punteggio < sano.punteggio
    assert any(i.livello == "critico" for i in difettoso.indicatori)


def test_limite_acidita_volatile_diverso_per_tipo():
    """Il limite UE e' 1,2 g/L per i rossi e 1,08 per i bianchi: lo stesso
    valore puo' essere accettabile in un rosso e critico in un bianco."""
    # 0,9 g/L e' l'83% del limite per i bianchi (critico) ma il 75% di quello
    # per i rossi (attenzione): cade esattamente fra i due.
    valore = 0.9
    rosso = valuta_conservazione(
        wine_type="red", free_sulfur_dioxide=30, total_sulfur_dioxide=90,
        ph=3.2, volatile_acidity=valore,
    )
    bianco = valuta_conservazione(
        wine_type="white", free_sulfur_dioxide=30, total_sulfur_dioxide=90,
        ph=3.2, volatile_acidity=valore,
    )
    liv_rosso = next(i.livello for i in rosso.indicatori if i.nome == "Acidita volatile")
    liv_bianco = next(i.livello for i in bianco.indicatori if i.nome == "Acidita volatile")
    assert liv_bianco == "critico"
    assert liv_rosso != "critico"


def test_indicatori_sempre_quattro_e_spiegati():
    c = valuta_conservazione(
        wine_type="white", free_sulfur_dioxide=30, total_sulfur_dioxide=100,
        ph=3.2, volatile_acidity=0.3,
    )
    assert len(c.indicatori) == 4
    assert all(i.spiegazione for i in c.indicatori)
    assert 0 <= c.punteggio <= 100


def test_totale_zero_non_esplode():
    """Difesa da una divisione per zero su dati sporchi."""
    c = valuta_conservazione(
        wine_type="red", free_sulfur_dioxide=0, total_sulfur_dioxide=0,
        ph=3.3, volatile_acidity=0.5,
    )
    assert 0 <= c.punteggio <= 100
