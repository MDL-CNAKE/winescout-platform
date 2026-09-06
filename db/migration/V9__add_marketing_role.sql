-- Ruolo marketing e strategia.
--
-- Il ruolo esiste, la sua sezione e' quasi vuota, e la ragione va detta:
-- le analisi commerciali richiedono uno storico di vendite che questa
-- piattaforma non possiede. WineScout conosce la chimica dei lotti, la
-- qualita' e un prezzo derivato; non conosce un solo ordine, cliente,
-- canale o data.
--
-- La pagina /marketing dichiara per ciascuna funzione quale dato le
-- servirebbe, invece di mostrare un cruscotto riempito di numeri
-- plausibili. E' la stessa scelta fatta altrove nel progetto: non
-- inventare vitigni assenti dal dataset, non dedurre preferenze di mercato
-- da dati che non le contengono.
--
-- Le sezioni visibili sono definite nel frontend (PER_RUOLO in
-- router.tsx); qui si estende soltanto il dominio ammesso.
ALTER TABLE operators
    MODIFY COLUMN role ENUM('titolare', 'enologo', 'vendite', 'logistica', 'marketing')
    NOT NULL DEFAULT 'titolare';

-- Allinea eventuali operatori gia' inseriti con questo nome.
UPDATE operators SET role = 'marketing' WHERE name = 'Marketing';
