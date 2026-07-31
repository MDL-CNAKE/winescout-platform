-- Selezioni di lavoro condivise all'interno della cantina.
--
-- L'applicazione e' installata da un singolo soggetto (la cantina), quindi
-- non esistono registrazione ne' autenticazione: chi la usa si dichiara
-- scegliendo il proprio nome da un elenco che la cantina configura. Non e'
-- un sistema di identita', e' un'etichetta di lavoro che serve a distinguere
-- le selezioni di persone diverse sulla stessa installazione.

CREATE TABLE operators (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(60)  NOT NULL,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_operator_name UNIQUE (name)
);

-- Ruoli invece di nomi di persona: sono validi per qualsiasi cantina e non
-- introducono dati inventati su individui. Modificabili dall'applicazione.
INSERT INTO operators (name) VALUES ('Titolare'), ('Enologo'), ('Vendite');

CREATE TABLE favorites (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    wine_id      INT       NOT NULL,
    operator_id  INT       NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Ogni operatore puo' segnare un vino una volta sola, ma piu' operatori
    -- possono segnare lo stesso vino: le selezioni restano distinte.
    CONSTRAINT uq_wine_operator UNIQUE (wine_id, operator_id),
    CONSTRAINT fk_fav_wine     FOREIGN KEY (wine_id)     REFERENCES wines(id)     ON DELETE CASCADE,
    CONSTRAINT fk_fav_operator FOREIGN KEY (operator_id) REFERENCES operators(id) ON DELETE CASCADE
);

CREATE INDEX idx_fav_wine ON favorites (wine_id);
