= Verifica semantica, un risultato negativo

== Il problema e il primo tentativo

Nei capitoli precedenti è stato mostrato che una query può essere eseguita
senza errori e restituire comunque una risposta sbagliata. Il sistema di
partenza controllava solo che il database non sollevasse eccezioni, quindi una
query valida ma mal formulata veniva considerata corretta. Serviva un controllo
sulla risposta e non sull'esecuzione.

La prima soluzione è stata aggiungere al grafo un nodo che usa un secondo
modello come revisore. Il nodo #raw("verify") riceve la domanda, la query
eseguita, le righe ottenute e la risposta proposta dall'agente, e decide se
approvarla o rifiutarla. Nel prompt sono stati elencati i casi da rifiutare,
per esempio una query che risponde a una domanda diversa, un risultato vuoto
riportato senza indagare, o un totale calcolato su righe troncate.

Il verdetto doveva inizialmente essere un oggetto strutturato, con un campo per
l'esito e uno per la motivazione. Questa strada è stata abbandonata perché il
modello non la rispettava in modo affidabile, rispondendo a volte in prosa
invece di produrre l'oggetto richiesto e altre volte restituendo la descrizione
del formato al posto di un valore. Il verdetto è quindi diventato una sola riga
di testo, che vale come approvazione solo se comincia con #raw("APPROVED") e in
ogni altro caso conta come rifiuto. Una risposta incomprensibile porta così a
una revisione in più e non a un'approvazione per sbaglio.

Se il verificatore rifiuta, la motivazione torna all'agente, che riformula la
risposta. Il numero di revisioni è limitato per evitare cicli infiniti.

== Il fallimento del verificatore

Il verificatore è stato provato sul caso descritto nel capitolo 3. Gli è stata
sottoposta una trascrizione in cui l'agente filtra su
#raw("country = 'Italy'"), ottiene zero righe e conclude che non ci sono
clienti italiani. La risposta è sbagliata, perché nel database il paese è
scritto #raw("IT").

Il verificatore ha approvato.

#figure(
  ```
  QUESTION: Quanti clienti italiani ci sono?
    called run_select({'sql': "SELECT COUNT(*) FROM customers WHERE country = 'Italy'"})
    returned: COUNT(*)
              0
              (1 rows)
  PROPOSED ANSWER: Non ci sono clienti italiani nel database.
  ```,
  caption: [La trascrizione sottoposta al verificatore, che ha risposto
  #raw("APPROVED").],
) <fig:verifica-fallita>

Il motivo è che il verificatore vede solo la query e le righe prodotte, e non
ha mai osservato il contenuto della colonna. Non può quindi sapere che il
valore #raw("Italy") non compare nei dati. Con una query corretta e un
risultato vuoto, la conclusione che non ci siano clienti italiani è plausibile.

Provato su altri casi, però, il verificatore si è comportato bene. Ha rifiutato
una risposta che contava cinquanta righe di un campione troncato come se
fossero il totale, e ne ha rifiutata una in cui la query contava i clienti
italiani mentre la domanda chiedeva quanto avessero speso. Il problema non era
quindi il verificatore, ma il tipo di controllo che gli veniva chiesto.

== La soluzione deterministica

Il controllo mancante non richiede interpretazione. Se una query filtra su un
valore testuale e non restituisce nulla, il risultato è ambiguo di per sé, e
per rilevarlo basta una regola.

Il controllo è stato quindi spostato dentro lo strumento #raw("run_select").
Quando una query non restituisce righe, lo strumento estrae i valori testuali
usati nei filtri e li segnala all'agente.

#figure(
  ```
  No rows returned. This query filters on the literal value(s) 'Italy'.
  An empty result looks the same whether nothing matches or the filter
  value is simply not written that way in the data. Use sample_rows to
  check how the column is actually written before reporting this as a
  finding.
  ```,
  caption: [Il messaggio che lo strumento restituisce al posto di un risultato
  vuoto.],
) <fig:avviso-literal>

Rispetto al verificatore questa soluzione scatta sempre, non dipende da come il
modello interpreta il prompt e non richiede una chiamata in più all'API. Arriva
inoltre mentre l'agente sta ancora lavorando, invece che dopo che la risposta è
stata formulata.

Il verificatore è stato mantenuto per i casi che richiedono interpretazione,
cioè proprio quelli che aveva superato, come una query che risponde a una
domanda diversa da quella posta o un totale calcolato su un campione. Le regole meccaniche stanno negli strumenti, il
giudizio nel verificatore.

Da questo episodio è derivato un criterio applicato anche altrove nel progetto.
I controlli che si possono esprimere come regola non vengono delegati al
modello, perché un modello linguistico valuta solo quello che ha davanti, e in
questo caso non aveva abbastanza informazioni per accorgersi dell'errore.
