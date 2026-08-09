"""Analisi esplorativa del dataset (EDA).

PERCHE' ARRIVA ADESSO E NON ALL'INIZIO
--------------------------------------
Nell'ordine canonico l'EDA viene prima del modello. Qui e' arrivata dopo, ed
e' un errore di metodo che vale la pena ammettere invece di nascondere
riordinando i file: si e' dato per scontato che un dataset accademico
pubblicato e citato fosse pulito.

Non lo era. Su 6.497 righe ce ne sono 1.177 perfettamente identiche - il 18%
del dataset - e questo ha una conseguenza diretta sulle metriche del modello,
misurata in src/models/leakage_experiment.py.

COSA GUARDA QUESTO SCRIPT
-------------------------
1. DUPLICATI. Righe con undici valori chimici identici. Non sono
   necessariamente un errore: due lotti dello stesso vino possono davvero
   avere la stessa analisi. Ma per un modello valutato con uno split casuale
   sono veleno, perche' la stessa riga puo' finire in addestramento e in test.

2. SBILANCIAMENTO. La distribuzione del target. Nei limiti del progetto era
   dichiarato "sbilanciato" senza mai mostrarlo: qui diventa un numero e un
   grafico.

3. CORRELAZIONI. Quali variabili si muovono con la qualita' e quali fra loro.
   Serve a leggere la permutation importance senza illudersi: due variabili
   molto correlate si rubano importanza a vicenda.

4. VALORI ANOMALI. Quanti punti stanno oltre 1.5 volte lo scarto
   interquartile, per variabile.

I grafici finiscono in docs/eda/ e sono pensati per essere guardati, non per
decorare: ognuno risponde a una domanda scritta sopra.

Uso: python src/eda.py
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path

import matplotlib

# Backend non interattivo: lo script gira anche dentro un container, dove non
# esiste nessuna finestra da aprire. Va impostato PRIMA di importare pyplot.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

CSV = "data/wine_quality_merged.csv"
USCITA = Path("docs/eda")

CHIMICHE = [
    "fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
    "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide",
    "density", "pH", "sulphates", "alcohol",
]


def carica() -> pd.DataFrame:
    return pd.read_csv(CSV)


def duplicati(df: pd.DataFrame) -> dict:
    """Quantifica le righe ripetute.

    Si distinguono due casi, e la differenza e' informativa:
    - stessa chimica E stessa qualita': copie perfette;
    - stessa chimica ma qualita' DIVERSA: due assaggiatori che hanno dato
      voti diversi allo stesso vino. Sono la prova che il target contiene
      rumore irriducibile - nessun modello puo' predire due valori diversi a
      partire dallo stesso input, quindi esiste un tetto all'R2 raggiungibile.
    """
    dup_completi = int(df.duplicated().sum())
    dup_chimica = int(df.duplicated(subset=CHIMICHE).sum())

    # Gruppi di righe con chimica identica ma qualita' discordante.
    gruppi = df.groupby(CHIMICHE)["quality"].nunique()
    contraddittori = int((gruppi > 1).sum())

    return {
        "righe": len(df),
        "duplicati_completi": dup_completi,
        "duplicati_chimica": dup_chimica,
        "percentuale": 100 * dup_completi / len(df),
        "gruppi_con_qualita_discordante": contraddittori,
        "righe_uniche": len(df.drop_duplicates()),
    }


def grafico_distribuzione(df: pd.DataFrame) -> None:
    """Quanto e' sbilanciato il target?

    Risponde alla domanda: il modello ha abbastanza esempi per imparare a
    riconoscere un vino eccellente? La risposta si legge a colpo d'occhio.
    """
    fig, ax = plt.subplots(figsize=(8, 4.5))
    conteggi = df["quality"].value_counts().sort_index()

    barre = ax.bar(conteggi.index, conteggi.values, color="#6d1b2f")
    for x, v in zip(conteggi.index, conteggi.values):
        ax.text(x, v + 40, str(v), ha="center", fontsize=9, color="#4a1220")

    ax.set_xlabel("Qualita' (0-10)")
    ax.set_ylabel("Numero di vini")
    ax.set_title(
        "Il target e' concentrato sul centro scala\n"
        "Le classi estreme hanno pochissimi esempi: il modello impara sopratutto la media",
        fontsize=10,
    )
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(USCITA / "distribuzione_qualita.png", dpi=130)
    plt.close(fig)


def grafico_correlazioni(df: pd.DataFrame) -> None:
    """Quali variabili si muovono insieme?

    Due usi distinti: capire cosa spiega la qualita', e capire quali coppie di
    variabili sono ridondanti - perche' fra variabili correlate l'importanza
    si divide, e una puo' sembrare inutile solo perche' l'altra la copre.
    """
    corr = df[CHIMICHE + ["quality"]].corr()

    fig, ax = plt.subplots(figsize=(9, 7.5))
    sns.heatmap(
        corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
        annot_kws={"size": 7}, cbar_kws={"label": "correlazione di Pearson"}, ax=ax,
    )
    ax.set_title("Correlazioni fra variabili chimiche e qualita'", fontsize=11)
    fig.tight_layout()
    fig.savefig(USCITA / "correlazioni.png", dpi=130)
    plt.close(fig)


def grafico_alcol_qualita(df: pd.DataFrame) -> None:
    """L'alcol e' la variabile piu' correlata con la qualita': quanto separa?

    Un boxplot mostra cio' che il coefficiente di correlazione nasconde: la
    sovrapposizione fra le classi. Se le scatole si accavallano, l'alcol da
    solo non basta a distinguere un vino buono da uno mediocre.
    """
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.boxplot(data=df, x="quality", y="alcohol", hue="type",
                palette={"red": "#6d1b2f", "white": "#d8c9a3"}, ax=ax)
    ax.set_xlabel("Qualita'")
    ax.set_ylabel("Alcol (% vol)")
    ax.set_title(
        "L'alcol sale con la qualita', ma le distribuzioni si sovrappongono:\n"
        "da solo non separa le classi",
        fontsize=10,
    )
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(USCITA / "alcol_per_qualita.png", dpi=130)
    plt.close(fig)


def anomalie(df: pd.DataFrame) -> pd.DataFrame:
    """Conta i punti oltre 1.5 IQR, per variabile.

    Non vengono rimossi: in enologia un valore estremo e' spesso un lotto
    reale e problematico, non un errore di misura, ed e' proprio quello che
    interessa a chi lavora in cantina. Il conteggio serve a sapere quanto
    pesano sulle statistiche, non a giustificarne la cancellazione.
    """
    righe = []
    for col in CHIMICHE:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        fuori = ((df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)).sum()
        righe.append({"variabile": col, "anomali": int(fuori),
                      "percentuale": round(100 * fuori / len(df), 1)})
    return pd.DataFrame(righe).sort_values("anomali", ascending=False)


def main() -> None:
    USCITA.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", font_scale=0.9)

    df = carica()

    print("=" * 68)
    print("DUPLICATI")
    print("=" * 68)
    d = duplicati(df)
    print(f"righe totali:                      {d['righe']}")
    print(f"righe uniche:                      {d['righe_uniche']}")
    print(f"duplicati completi:                {d['duplicati_completi']} "
          f"({d['percentuale']:.1f}% del dataset)")
    print(f"duplicati sulla sola chimica:      {d['duplicati_chimica']}")
    print(f"gruppi con qualita' discordante:   {d['gruppi_con_qualita_discordante']}")
    print()
    # Il commento si adatta al dato invece di anticiparlo. L'ipotesi iniziale
    # era che esistessero vini con la stessa chimica e voti diversi - cioe'
    # assaggiatori in disaccordo - e i dati l'hanno smentita. Stampare
    # comunque la spiegazione preparata sarebbe stato esattamente l'errore
    # che questa analisi esiste per evitare.
    if d["gruppi_con_qualita_discordante"] > 0:
        print("Stessa chimica con voti diversi: il target contiene rumore")
        print("irriducibile, perche' nessun modello puo' predire due valori")
        print("diversi dallo stesso input. Esiste quindi un tetto all'R2.")
    else:
        print("Nessuna contraddizione: a chimica identica corrisponde sempre")
        print("lo stesso voto. I duplicati sono copie esatte, non giudizi")
        print("discordanti - il che li rende innocui per la coerenza del")
        print("target e pericolosi per la valutazione, perche' una copia in")
        print("test e' una risposta gia' vista in addestramento.")

    print()
    print("=" * 68)
    print("DISTRIBUZIONE DEL TARGET")
    print("=" * 68)
    conteggi = df["quality"].value_counts().sort_index()
    for q, n in conteggi.items():
        print(f"  qualita' {q}: {n:5d}  ({100 * n / len(df):5.1f}%)  {'#' * (n // 60)}")
    centro = conteggi.get(5, 0) + conteggi.get(6, 0)
    print(f"\nLe sole classi 5 e 6 valgono il {100 * centro / len(df):.1f}% del dataset.")
    print("Un modello che predicesse sempre 5.6 sbaglierebbe poco: e' il")
    print("riferimento minimo contro cui va giudicato ogni risultato.")

    print()
    print("=" * 68)
    print("CORRELAZIONI CON LA QUALITA'")
    print("=" * 68)
    corr = df[CHIMICHE + ["quality"]].corr()["quality"].drop("quality")
    for var, val in corr.sort_values(key=abs, ascending=False).items():
        print(f"  {var:24s} {val:+.3f}")

    print()
    print("=" * 68)
    print("VALORI ANOMALI (oltre 1.5 IQR)")
    print("=" * 68)
    print(anomalie(df).to_string(index=False))

    grafico_distribuzione(df)
    grafico_correlazioni(df)
    grafico_alcol_qualita(df)
    print(f"\nGrafici salvati in {USCITA}/")


if __name__ == "__main__":
    main()
