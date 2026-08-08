-- Ruoli operativi e profili di mercato.
--
-- RUOLI
-- Non sono permessi di sicurezza: l'applicazione appartiene a una sola
-- cantina e chi la apre sceglie liberamente chi essere. Servono a mostrare
-- a ciascuno gli strumenti del proprio mestiere invece di tutto insieme:
-- l'enologo lavora sulla chimica, chi vende sui margini, il titolare vede
-- l'insieme.
ALTER TABLE operators
    ADD COLUMN role ENUM('titolare', 'enologo', 'vendite') NOT NULL DEFAULT 'titolare';

UPDATE operators SET role = 'enologo' WHERE name = 'Enologo';
UPDATE operators SET role = 'vendite' WHERE name = 'Vendite';

-- PROFILI DI MERCATO
--
-- Il dataset non contiene geografia, clienti ne' storico vendite: nessun
-- dato permette di dedurre cosa piaccia in un certo mercato. La conoscenza
-- commerciale resta quindi umana — la dichiara chi vende — e il sistema fa
-- cio' che sa fare davvero: cercare fra 6497 lotti quelli che rispondono a
-- quel profilo chimico, ordinati per redditivita'.
--
-- Ogni vincolo e' facoltativo (NULL = non filtra): un profilo puo' essere
-- generico ("bianchi sotto i 15 euro") o molto stretto.
CREATE TABLE market_profiles (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(80)  NOT NULL,
    notes         VARCHAR(300) NULL,
    wine_type     ENUM('red', 'white') NULL,
    min_quality   TINYINT      NULL,
    min_alcohol   DECIMAL(5,2) NULL,
    max_alcohol   DECIMAL(5,2) NULL,
    max_sugar     DECIMAL(6,2) NULL,
    min_acidity   DECIMAL(5,2) NULL,
    max_price     DECIMAL(7,2) NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_profile_name UNIQUE (name)
);

-- Esempi plausibili, modificabili e cancellabili dall'applicazione: servono
-- a far capire il meccanismo alla prima apertura, non sono dati di mercato.
INSERT INTO market_profiles (name, notes, wine_type, min_quality, max_alcohol, max_sugar, min_acidity, max_price) VALUES
    ('Nord Europa - bianchi freschi',
     'Richiesta di bianchi secchi e agili, buona acidita, gradazione contenuta.',
     'white', 6, 12.0, 4.0, 6.5, 20.00),
    ('Ristorazione locale - rossi da tutto pasto',
     'Rossi di pronta beva per la carta a bicchiere, prezzo contenuto.',
     'red', 5, NULL, 4.0, NULL, 15.00);

INSERT INTO market_profiles (name, notes, wine_type, min_quality, min_alcohol, max_price) VALUES
    ('Enoteche - selezione premium',
     'Referenze di punta per il canale specializzato, struttura e punteggio alti.',
     NULL, 7, 12.0, NULL);
