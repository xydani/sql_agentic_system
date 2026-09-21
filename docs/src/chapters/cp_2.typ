= Il sistema di partenza

== Funzionamento

Il progetto di partenza traduce una domanda in linguaggio naturale in una query
SQL, la esegue su un database SQLite e restituisce le righe ottenute. È
composto da cinque file.

#raw("schema_utils.py") legge la struttura del database e la trasforma in un
blocco di testo che elenca tabelle, colonne e chiavi esterne. Questo testo
viene inserito nel prompt come contesto, perché il modello non ha altro modo di
sapere com'è fatto il database.

#raw("nl2sql_agent.py") invia la richiesta al modello linguistico e ne estrae
la query, che il modello restituisce dentro un blocco di codice. La classe
mantiene lo storico dei messaggi scambiati.

#raw("db_executor.py") esegue la query, ma non nel processo principale. La
esegue in un sottoprocesso separato, così una query che si blocca può essere
interrotta con un timeout senza fermare il resto del programma.
#raw("_db_worker.py") è lo script eseguito da quel sottoprocesso.

#raw("main.py") contiene il ciclo che lega tutto. Genera la query, la esegue e,
se l'esecuzione fallisce, ripete fino a un massimo di quattro tentativi.

#figure(
  ```
  domanda --> [agente: genera SQL] --> [executor: esegue] --> righe
                      ^                        |
                      |____ errore del DB _____|   (max 4 tentativi)
  ```,
  caption: [Il flusso del sistema di partenza.],
) <fig:pipeline-originale>

La parte più interessante del sistema è il modo in cui gestisce gli errori.
Quando una query fallisce, il messaggio di errore del database non viene
scartato ma aggiunto alla stessa conversazione. Al tentativo successivo il
modello vede la query che aveva scritto e l'errore esatto che ha causato,
quindi non riparte da zero ma corregge. Questo meccanismo è stato mantenuto
anche nel sistema nuovo.

== Difetti rilevati

Durante l'analisi del codice sono emersi alcuni problemi, alcuni dei quali
rilevanti per il seguito del lavoro.

Il primo riguarda il controllo sulle scritture. #raw("db_executor.py") rifiuta
le query che iniziano con una parola presente in una lista, che contiene
#raw("DROP"), #raw("DELETE"), #raw("UPDATE"), #raw("ALTER"), #raw("INSERT") e
#raw("TRUNCATE"). Il controllo guarda però solo la prima parola, e la lista non
comprende tutti i comandi che modificano il database.

#figure(
  table(
    columns: (1fr, auto),
    align: (left, left),
    stroke: (x, y) => if y == 0 { (bottom: 0.5pt) } else { none },
    [*Query provata*], [*Esito*],
    [`DROP TABLE customers`], [bloccata],
    [`-- commento` \ `DROP TABLE customers`], [eseguita],
    [`CREATE TABLE evil (x INT)`], [eseguita],
    [`REPLACE INTO customers VALUES (...)`], [eseguita],
    [`ATTACH DATABASE '/etc/passwd' AS p`], [eseguita],
    [`PRAGMA table_info(customers)`], [eseguita],
  ),
  caption: [Query provate contro il controllo del sistema di partenza. Solo la
  prima viene effettivamente bloccata.],
) <tab:aggiramenti>

Un secondo problema riguarda il parametro #raw("allow_writes"). Quando è
attivo la query di scrittura viene eseguita, ma la connessione viene chiusa
senza chiamare #raw("commit"), quindi la modifica va persa. La funzione non ha
quindi mai funzionato.

Il terzo problema è l'assenza di un limite sulle righe restituite. Sul database
di esempio non si nota, perché contiene sette righe in tutto, ma su una tabella
grande il risultato verrebbe caricato per intero in memoria e inserito nel
prompt.

Restano infine due imprecisioni minori. La documentazione di #raw("main.py")
indica una variabile d'ambiente diversa da quella effettivamente usata dal
codice, e #raw("nl2sql_agent.py") stampa l'intera conversazione a ogni chiamata
al modello.
