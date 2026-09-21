= Risultati

== Il confronto con il sistema di partenza

Il programma mette a disposizione un'opzione che risponde alla stessa domanda
con i due sistemi, uno dopo l'altro. Entrambi usano lo stesso modello
linguistico, quindi l'unica differenza fra le due risposte è l'architettura.
L'esempio seguente usa il database fornito con il progetto, che contiene tre
clienti di cui uno italiano.

#figure(
  ```
  Question: Quanti clienti italiani ci sono?

  --- before: fixed pipeline, retries only on SQL errors ---
    SELECT COUNT(*) AS num_italian_customers
  FROM customers
  WHERE country = 'Italy'
    num_italian_customers
  0
  (1 rows)

  --- after: agent that inspects the database ---
    C'è 1 cliente italiano (country = 'IT').

    steps taken:
      list_tables({})
      describe_table({'table': 'customers'})
      sample_rows({'table': 'customers'})
      run_select({'sql': "SELECT COUNT(*) AS n FROM customers
                          WHERE country = 'IT'"})
  ```,
  caption: [Le due risposte alla stessa domanda, con la traccia degli strumenti
  usati dall'agente. Le etichette stampate dal programma sono in inglese.],
) <fig:confronto>

Il sistema di partenza scrive un filtro sul nome esteso del paese, ottiene zero
righe e si ferma, perché l'esecuzione non ha prodotto errori. Il sistema
agentico guarda prima quali tabelle esistono, poi le colonne di
#raw("customers"), poi alcune righe reali, e solo a quel punto scrive la query
usando il valore che ha trovato nei dati.

La traccia mostra che nessuno di quei passi è previsto dal codice. È il modello
a scegliere quali strumenti usare e in quale ordine.

== Le prove sul database esteso

Il database fornito con il progetto contiene due tabelle e sette righe in
tutto, il che basta per la dimostrazione ma non per verificare che il sistema
regga su dati realistici. È stato quindi costruito un secondo database, con
quattro tabelle e circa millecinquecento righe, generato da un seme fisso e
quindi riproducibile in modo identico. Al suo interno sono state inserite
apposta alcune difficoltà che si incontrano nei dati veri.

#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    stroke: (x, y) => if y == 0 { (bottom: 0.5pt) } else { none },
    [*Difficoltà*], [*Perché conta*],
    [#raw("country") contiene codici],
    [un filtro sul nome esteso restituisce zero righe senza errori],
    [#raw("status") contiene lettere],
    [il significato dei codici va ricavato guardando i dati],
    [colonne che possono essere nulle],
    [contare una colonna e contare le righe dà risultati diversi],
    [#raw("name") esiste in due tabelle],
    [le unioni fra tabelle devono indicare quale colonna usare],
    [#raw("unit_price") esiste in due tabelle],
    [il fatturato va calcolato sul prezzo dell'ordine, non su quello corrente],
    [circa millecinquecento righe],
    [i risultati vengono troncati e non vanno contati come totali],
  ),
  caption: [Le difficoltà inserite nel database di valutazione.],
) <tab:trappole>

Sono state poi provate cinque domande di difficoltà crescente, ripetute tre
volte ciascuna su entrambi i sistemi per un totale di trenta esecuzioni. La
risposta è stata confrontata con il valore calcolato direttamente sul database.
Il confronto è automatico e tiene conto del fatto che la risposta è in
linguaggio naturale, quindi estrae i numeri dal testo invece di cercare una
corrispondenza esatta. Anche la valutazione è uno script del progetto, e può
essere rieseguita.

#figure(
  table(
    columns: (1fr, auto, auto, auto),
    align: (left, right, center, center),
    stroke: (x, y) => if y == 0 { (bottom: 0.5pt) } else { none },
    [*Domanda*], [*Atteso*], [*Agentico*], [*Di partenza*],
    [Quanti clienti italiani ci sono], [40], [3/3], [0/3],
    [Quanti ordini sono stati annullati], [36], [3/3], [0/3],
    [Quanti clienti non hanno email], [20], [3/3], [3/3],
    [Quanti clienti tedeschi ci sono], [24], [3/3], [0/3],
    [Fatturato esclusi gli annullati], [741458,03], [3/3], [0/3],
    table.hline(stroke: 0.5pt),
    [*Totale*], [], [*15/15*], [*3/15*],
  ),
  caption: [Risposte corrette su tre ripetizioni per domanda.],
) <tab:domande>

L'unica domanda a cui il sistema di partenza risponde correttamente è quella
sui clienti senza email, che è anche l'unica a non richiedere di sapere come
sono scritti i valori nelle colonne. Nelle altre il filtro viene costruito sul
nome esteso del paese o sullo stato dell'ordine, e il risultato è zero.

Il caso del fatturato è diverso e merita attenzione. Il sistema di partenza non
restituisce zero ma 807486,86, cioè il fatturato comprensivo degli ordini
annullati, perché non ha modo di sapere che la lettera #raw("X") indica un
annullamento. La risposta è plausibile, non è segnalata da alcun errore ed è
sbagliata di circa sessantaseimila. È il caso peggiore dei due, perché nulla
invita a controllarla.

La domanda sul fatturato è anche la più impegnativa per l'agente, perché
richiede di unire tre tabelle, di escludere gli ordini annullati riconoscendo
che lo stato è indicato da una lettera, e di usare il prezzo registrato sulla
riga dell'ordine invece di quello corrente del prodotto. Il significato dei
codici di stato non è scritto da nessuna parte, e l'agente lo ha ricavato
campionando la tabella.

Le domande sono state però scritte da chi ha costruito il database di
valutazione, quindi il confronto misura quanto i due sistemi affrontano le
difficoltà previste e non quanto se la caverebbero su dati raccolti da altri.
Il limite è ripreso nel capitolo 9.

== I test automatici

Il progetto ha centoventisette test automatici, che si eseguono senza bisogno di
una chiave API. Coprono il controllo sulle scritture, comprese le query che
aggiravano quello del sistema di partenza, la lettura dello schema, il
comportamento degli strumenti e l'interfaccia a riga di comando.

La parte più utile riguarda il grafo, provato sostituendo al modello
linguistico un oggetto che restituisce risposte prestabilite. In questo modo
l'approvazione, il rifiuto con ritorno all'agente, il limite alle revisioni, la
separazione fra conversazioni diverse e l'autocorrezione su un errore SQL sono
verificati in modo deterministico, senza dipendere da cosa risponde il modello.
