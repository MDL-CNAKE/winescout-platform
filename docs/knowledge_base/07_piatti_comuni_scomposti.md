# Piatti comuni scomposti nelle loro sensazioni

Questo documento esiste per colmare un divario misurato, non supposto. La
valutazione del retrieval (`python src/rag/evaluate.py`) mostrava tre domande
che fallivano con OGNI strategia — semantica, lessicale e ibrida: carbonara,
tiramisu, prosciutto crudo. Il motivo era comune: la knowledge base descrive
SENSAZIONI (grassezza, sapidita, tendenza dolce) mentre chi chiede nomina
PIATTI. Nessun aggiustamento dell'algoritmo puo' colmare un divario che sta
nei dati.

Il metodo di abbinamento resta quello sensoriale: qui non si aggiungono regole
nuove, si costruisce il ponte fra il nome di un piatto e le sensazioni che gia'
sappiamo trattare.

## Primi piatti

CARBONARA: grassezza marcata (guanciale, uovo, pecorino), sapidita alta,
tendenza dolce della pasta. Chiede acidita e freschezza per pulire il palato,
oppure effervescenza.

CACIO E PEPE: grassezza del pecorino, sapidita molto alta, nota piccante dal
pepe. Serve un vino fresco e sapido, non morbido.

RAGU DI CARNE: succulenza, tendenza dolce del pomodoro cotto e della carne,
leggera grassezza. Chiede un rosso di media struttura con buona acidita.

PASTA AL PESTO: untuosita dell'olio, tendenza amara del basilico e dei pinoli,
sapidita del formaggio. Un bianco fresco e non aromatico.

RISOTTO ALLA MILANESE: grassezza da mantecatura, tendenza dolce del riso,
leggera nota amara dello zafferano.

LASAGNE: grassezza della besciamella, sapidita, succulenza. Rosso di corpo
medio con acidita sostenuta.

## Carni

BISTECCA AL SANGUE: succulenza molto alta, sapidita, leggera tendenza dolce
della carne rossa. Chiede tannino e struttura.

BRASATO E STUFATI: succulenza alta, tendenza dolce da cottura lunga,
grassezza. Rosso strutturato.

POLLO ARROSTO: succulenza media, tendenza dolce, grassezza della pelle.
Regge sia bianchi strutturati sia rossi leggeri.

SALUMI E PROSCIUTTO CRUDO: sapidita molto alta, grassezza del lardello,
tendenza dolce nel crudo stagionato dolce. Chiede acidita e, se serve,
effervescenza per pulire.

ARROSTO DI MAIALE: grassezza e succulenza insieme, tendenza dolce.

## Pesce

FRITTURA DI PESCE: untuosita marcata dalla frittura, sapidita. Il caso tipico
da contrapporre con acidita ed effervescenza.

PESCE ALLA GRIGLIA: sapidita, leggera tendenza amara dalla bruciatura,
succulenza modesta. Bianco fresco e non invadente.

CRUDI DI MARE: sapidita e leggera dolcezza naturale, nessuna grassezza.
Bianco molto fresco, mai morbido.

BACCALA MANTECATO: grassezza e sapidita alte insieme.

## Verdure e formaggi

RADICCHIO, CARCIOFI, CICORIA: tendenza amara marcata. L'amaro del cibo si
somma all'amaro del vino, quindi si evitano vini tannici o molto amari.

FORMAGGI STAGIONATI: sapidita e grassezza alte, a volte nota piccante.

FORMAGGI ERBORINATI: sapidita, grassezza, piccantezza. E' il caso in cui la
concordanza con un vino dolce funziona meglio della contrapposizione.

VERDURE GRIGLIATE: tendenza amara e leggera dolcezza da caramellizzazione.

## Dolci

TIRAMISU: dolcezza vera, grassezza del mascarpone, tendenza amara del caffe.
Chiede CONCORDANZA con un vino dolce: un vino secco accanto a un dolce sembra
acido e spoglio.

DOLCI AL CIOCCOLATO: dolcezza e tendenza amara insieme, grassezza del burro di
cacao. Concordanza con vini dolci strutturati.

CROSTATE DI FRUTTA: dolcezza moderata, acidita della frutta.

PASTICCERIA SECCA: dolcezza, tendenza dolce, poca grassezza.

## Cucine non europee

CURRY INDIANO: piccantezza marcata, grassezza (latte di cocco, burro
chiarificato), tendenza dolce delle spezie. La piccantezza si spegne con
morbidezza e dolcezza, non con l'alcol, che la amplifica.

SUSHI E SASHIMI: sapidita, leggera dolcezza del riso, nessuna grassezza nei
pesci magri.

KIMCHI E FERMENTATI: sapidita e acidita gia presenti nel cibo, piccantezza.

COUSCOUS E TAJINE: tendenza dolce della frutta secca, sapidita, spezie dolci.

TACOS E CUCINA MESSICANA: piccantezza, grassezza, sapidita.

Il metodo vale su qualsiasi cucina: si scompone il piatto nelle sensazioni e
si applicano contrapposizione e concordanza. Vedi l'esempio del ndole.
