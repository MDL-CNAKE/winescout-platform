"""Test per src/levers.py: analisi controfattuale delle leve di miglioramento."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.levers import LEVE, FEATURE_ORDER, analizza_leve


class ModelloFinto:
    """Modello prevedibile: la qualita' cresce con l'alcol e cala con
    l'acidita' volatile. Permette di verificare la logica delle leve senza
    dipendere dal modello reale addestrato."""

    def predict(self, df):
        return (df["alcohol"] * 0.5 - df["volatile_acidity"] * 2.0).to_numpy()


def vino_base() -> dict:
    return {
        "type": "red", "fixed_acidity": 7.0, "volatile_acidity": 0.5,
        "citric_acid": 0.3, "residual_sugar": 2.0, "chlorides": 0.08,
        "free_sulfur_dioxide": 15.0, "total_sulfur_dioxide": 100.0,
        "density": 0.997, "ph": 3.3, "sulphates": 0.6, "alcohol": 10.0,
    }


def test_individua_la_direzione_giusta():
    """Con un modello che premia l'alcol e penalizza l'acidita' volatile, le
    leve devono proporre di aumentare il primo e ridurre la seconda."""
    _, leve = analizza_leve(ModelloFinto(), vino_base())
    per_campo = {l.campo: l for l in leve}

    assert per_campo["alcohol"].direzione == "aumentare"
    assert per_campo["volatile_acidity"].direzione == "ridurre"


def test_ordinate_per_guadagno_decrescente():
    _, leve = analizza_leve(ModelloFinto(), vino_base())
    guadagni = [l.delta_qualita for l in leve]
    assert guadagni == sorted(guadagni, reverse=True)


def test_scarta_le_leve_che_non_migliorano():
    """Il modello finto ignora gli altri parametri: quelle leve non portano
    guadagno e non devono comparire."""
    _, leve = analizza_leve(ModelloFinto(), vino_base())
    campi = {l.campo for l in leve}
    assert campi <= {"alcohol", "volatile_acidity"}
    assert all(l.delta_qualita > 0 for l in leve)


def test_rispetta_i_limiti_fisiologici():
    """Un vino gia' al massimo di alcol non puo' ricevere il consiglio di
    aumentarlo oltre il limite del dominio."""
    w = vino_base()
    w["alcohol"] = 15.0  # massimo previsto dalla leva
    _, leve = analizza_leve(ModelloFinto(), w)
    alcol = [l for l in leve if l.campo == "alcohol"]
    assert alcol == []


def test_nessuna_leva_e_un_esito_valido():
    """Se nulla migliora, la lista e' vuota: non si inventa un consiglio."""
    class Piatto:
        def predict(self, df):
            return [5.0] * len(df)

    base, leve = analizza_leve(Piatto(), vino_base())
    assert leve == []
    assert base == 5.0


def test_passi_realistici():
    """I passi devono restare correzioni applicabili in cantina: se qualcuno
    li gonfiasse, l'analisi produrrebbe numeri grandi e inutilizzabili."""
    per_campo = {l.campo: l for l in LEVE}
    assert per_campo["alcohol"].passo <= 1.0
    assert per_campo["volatile_acidity"].passo <= 0.2
    assert per_campo["ph"].passo <= 0.1


def test_tutte_le_leve_sono_feature_del_modello():
    assert all(l.campo in FEATURE_ORDER for l in LEVE)
