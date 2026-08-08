-- Ruolo logistica.
--
-- Chi gestisce magazzino e spedizioni non ha bisogno del profilo chimico
-- ne' dei margini: guarda cosa c'e' a catalogo, come e' confezionato e
-- cosa deve partire. Le sezioni visibili sono definite nel frontend
-- (PER_RUOLO in router.tsx); qui si estende soltanto il dominio ammesso.
ALTER TABLE operators
    MODIFY COLUMN role ENUM('titolare', 'enologo', 'vendite', 'logistica')
    NOT NULL DEFAULT 'titolare';

-- Allinea gli operatori gia' inseriti con quel nome, creati prima che il
-- ruolo esistesse.
UPDATE operators SET role = 'logistica' WHERE name = 'Logistica';
