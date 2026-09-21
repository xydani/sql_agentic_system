= Progettazione del sistema agentico

== L'architettura a grafo

Il sistema è descritto come un grafo con tre nodi e due cicli. La struttura è
dichiarata nel codice, e il comando #raw("main.py --diagram") la esporta in
formato Mermaid a partire dal grafo compilato, quindi lo schema della figura
corrisponde a ciò che viene effettivamente eseguito.

#figure(
  ```
                      inizio
                         |
                         v
                  +-------------+   chiamate   +-----------+
                  |    agent    | -----------> |   tools   |
                  |             | <----------- |           |
                  +------+------+   risultati  +-----------+
                         |
                         | nessuna chiamata
                         v
                  +-------------+
                  |   verify    |
                  +------+------+
                         |
                +--------+--------+
                |                 |
             rifiuto          approvato
                |                 |
                v                 v
              agent              fine
  ```,
  caption: [Il grafo del sistema agentico.],
) <fig:grafo>

Il nodo #raw("agent") è il modello linguistico con gli strumenti collegati. A
ogni passaggio decide se chiamare uno strumento oppure se ha già abbastanza
informazioni per rispondere. Il nodo #raw("tools") esegue le chiamate richieste
e ne restituisce i risultati, compresi i messaggi di errore del database. Il
nodo #raw("verify") riceve la risposta proposta e decide se approvarla.

Lo stato condiviso fra i nodi contiene tre campi. Il campo #raw("messages")
raccoglie la conversazione e cresce a ogni passaggio. Il campo
#raw("revisions") conta quante volte la risposta è stata rifiutata, così il
ciclo di revisione non prosegue all'infinito. Il campo #raw("approved")
registra l'esito della verifica.

Gli archi che escono da #raw("agent") e da #raw("verify") sono condizionali,
cioè il passo successivo viene scelto da una funzione che guarda lo stato. Dopo
#raw("agent") si va a #raw("tools") se il modello ha chiesto uno strumento,
altrimenti a #raw("verify"). Dopo #raw("verify") si termina se la risposta è
approvata o se le revisioni sono esaurite, altrimenti si torna a
#raw("agent").

Da qui nascono i due cicli. Il primo, fra #raw("tools") e #raw("agent"), è il
meccanismo di autocorrezione del sistema di partenza riportato dentro il grafo.
Quando una query fallisce l'errore torna al modello come risultato dello
strumento, e il modello corregge. Il secondo ciclo, fra #raw("verify") e
#raw("agent"), è nuovo e serve ai casi in cui la query è stata eseguita senza
errori ma la risposta non convince. In quel caso la motivazione del rifiuto
viene aggiunta alla conversazione e l'agente riparte da lì.

Il grafo è infine compilato con un checkpointer, che conserva lo stato di ogni
conversazione. Questo permette di fare domande di seguito. Dopo aver chiesto
quanti sono i clienti italiani, alla domanda #emph[e per il Regno Unito?]
l'agente non riesplora lo schema ma scrive direttamente la query, passando da
quattro chiamate a una.

== Gli strumenti

L'agente dispone di quattro strumenti, ognuno dei quali richiama funzioni che
esistevano già nel sistema di partenza.

#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    stroke: (x, y) => if y == 0 { (bottom: 0.5pt) } else { none },
    [*Strumento*], [*Cosa fa*],
    [`list_tables`], [elenca i nomi delle tabelle],
    [`describe_table`], [mostra colonne, tipi e chiavi di una tabella],
    [`sample_rows`], [mostra alcune righe reali di una tabella],
    [`run_select`], [esegue una query di lettura e restituisce le righe oppure
    l'errore del database],
  ),
  caption: [Gli strumenti a disposizione dell'agente.],
) <tab:strumenti>

Ogni strumento ha una breve descrizione scritta in inglese. Quella descrizione
non serve a chi legge il codice, ma viene inviata al modello insieme alla
domanda a ogni chiamata. Il modello infatti non vede il codice Python degli
strumenti, ma solo il loro nome, i parametri che accettano e appunto la
descrizione, che è quindi l'unica cosa su cui può basarsi per capire quale
strumento gli serve. Cambiarla cambia il comportamento dell'agente, quindi fa
parte del programma a tutti gli effetti. Un esempio è la descrizione di #raw("sample_rows"), che avverte il modello che una colonna può contenere #raw("IT") invece di #raw("Italy"). È questa frase a spingerlo a guardare i dati prima di filtrare.
