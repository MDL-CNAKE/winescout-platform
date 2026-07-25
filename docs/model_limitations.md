# Limiti del modello e sbilanciamento dei dati

## Distribuzione del target (qualità)

Il dataset Wine Quality (UCI) è fortemente sbilanciato sul punteggio di qualità:

| Qualità | N. vini | % sul totale |
|:---:|:---:|:---:|
| 3 | 30 | 0.5% |
| 4 | 216 | 3.3% |
| 5 | 2138 | 32.9% |
| 6 | 2836 | 43.7% |
| 7 | 1079 | 16.6% |
| 8 | 193 | 3.0% |
| 9 | 5 | 0.1% |

Le classi centrali 5 e 6 rappresentano da sole il **76.6%** dei campioni,
mentre gli estremi (vini scadenti o eccellenti) sono rari: la qualità 3 è lo
0.5% e la qualità 9 conta appena 5 vini su 6497.

## Impatto sul modello

Il problema affrontato è di **regressione** (predizione di un punteggio
continuo 3-9), non di classificazione. Per questo motivo il parametro
`class_weight` — citato dalla traccia come esempio di gestione dello
sbilanciamento — **non è applicabile**: è un parametro dei classificatori,
non dei regressori.

Lo sbilanciamento si riflette comunque sulle prestazioni: avendo pochissimi
esempi di vini eccellenti o scadenti, il modello tende a predire valori
vicini alla media (5-6), dove si concentra la quasi totalità dei dati.
Questo spiega perché l'R² si assesta intorno a 0.52: il modello coglie bene
la tendenza generale ma fatica sugli estremi, proprio quelli commercialmente
più interessanti (un vino eccellente o un difetto grave).

## Gestione adottata

Coerentemente con la natura del problema (regressione) e con la traccia
WineScout (che richiede esplicitamente un modello di regressione), lo
sbilanciamento è stato **riconosciuto e quantificato come limite noto**
anziché "corretto" con tecniche di classificazione non pertinenti.

Possibili sviluppi futuri per affrontarlo attivamente:
- pesare i campioni rari con `sample_weight` in fase di training;
- riformulare il problema come classificazione a 3 fasce
  (scarso / medio / ottimo) e usare `class_weight="balanced"`;
- raccogliere più dati sui vini agli estremi della scala qualitativa.

## Altri limiti noti

- **Bias geografico e tipologico**: il dataset contiene solo vini portoghesi
  fermi (rossi e bianchi Vinho Verde). Mancano rosati, spumanti, vini di
  altre regioni. Il modello non è affidabile fuori da questo dominio.
- **Dati commerciali simulati**: prezzo, margine, nome e abbinamento
  cibo-vino non provengono dal dataset originale (puramente chimico) ma sono
  generati con logiche esplicite e documentate (src/pricing.py, naming.py,
  pairing.py). Non sono dati reali di mercato.
- **Qualità come giudizio soggettivo**: il punteggio del dataset deriva da
  valutazioni sensoriali umane, intrinsecamente soggettive; nessun modello
  può replicarle con precisione perfetta.
