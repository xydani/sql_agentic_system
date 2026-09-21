= Conclusioni e sviluppi futuri

Il lavoro è partito da un sistema che traduceva una domanda in SQL e ritentava
quando il database restituiva un errore. Il risultato è un sistema in cui il
modello decide da solo quali strumenti usare e in quale ordine, guarda lo
schema e i dati prima di scrivere la query, e sottopone la propria risposta a
un controllo prima di restituirla. Il ciclo di orchestrazione scritto in Python
non esiste più, e la sequenza delle operazioni non è più prevedibile leggendo
il codice.

Il meccanismo di autocorrezione del sistema di partenza non è stato però
buttato. È stato riportato dentro il grafo, dove è diventato uno dei due cicli.

Dal capitolo 7 è uscito il risultato più utile del lavoro, che è anche un
risultato negativo. Affidare a un modello linguistico la verifica della
correttezza di una risposta non ha funzionato proprio nel caso che contava,
perché il verificatore non disponeva delle informazioni necessarie per
accorgersi dell'errore. Il controllo è stato riscritto come regola dentro lo
strumento, e al modello è rimasta la responsabilità dei soli casi che
richiedono interpretazione. Il criterio che ne deriva è di non delegare al
modello ciò che si può decidere in modo meccanico.

Resta utile distinguere due tipi di garanzia. I centoventisette test provano in
modo deterministico il comportamento del grafo e dei controlli, perché
sostituiscono al modello un oggetto che risponde in modo prestabilito. Le prove
del capitolo 8 invece osservano come si comporta il sistema con un modello
vero, su un numero limitato di esecuzioni. Le prime sono garanzie, le seconde
sono osservazioni, e confonderle porterebbe ad attribuire al sistema
un'affidabilità che non è stata misurata.

Gli sviluppi più sensati partono dai limiti del capitolo 9. Una valutazione su
benchmark pubblici toglierebbe il problema di avere scritto
le domande su misura per il sistema. Il supporto ad altri motori di database
richiede di riscrivere la lettura dello schema e il controllo sulle scritture,
lasciando il grafo invariato. Un'architettura con più agenti coordinati da un
supervisore, infine, si innesterebbe sul grafo esistente aggiungendo nodi,
senza doverlo ripensare.
