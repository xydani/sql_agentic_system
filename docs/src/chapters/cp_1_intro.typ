= Introduzione

Interrogare un database richiede di conoscere SQL e di sapere com'è fatto lo
schema. I sistemi text-to-SQL servono a togliere questo requisito, traducendo
una domanda scritta in linguaggio naturale in una query da eseguire. Con i
modelli linguistici recenti la traduzione riesce quasi sempre a produrre SQL
sintatticamente valido.

Il problema è che SQL valido non vuol dire SQL corretto. Una query può essere
eseguita senza errori e rispondere a una domanda diversa da quella posta,
oppure filtrare su un valore che nei dati non esiste. In entrambi i casi il
database non segnala nulla, e chi ha fatto la domanda riceve un numero
sbagliato senza avere motivo di dubitarne. È da qui che parte il lavoro
descritto in questa relazione.

Il progetto ha l'obiettivo di trasformare un sistema text-to-SQL già
funzionante in un sistema agentico. Il sistema di partenza era una pipeline fissa che generava una query, la
eseguiva e, in caso di errore, rimandava il messaggio del database al modello
perché si correggesse. Il meccanismo funziona, ma il modello non decide nulla e
non ha modo di guardare il database prima di scrivere la query.

La relazione segue l'ordine in cui il lavoro è stato svolto. I capitoli 2 e 3
descrivono il sistema di partenza e spiegano perché non può essere considerato
agentico. Il capitolo 4 confronta i framework disponibili e motiva la scelta.
I capitoli 5 e 6 descrivono la progettazione e la realizzazione del sistema
nuovo. Il capitolo 7 racconta un tentativo che non ha funzionato, cioè affidare
a un modello linguistico la verifica della correttezza delle risposte, e la
soluzione che ne è nata. Il capitolo 8 riporta i risultati, il 9 i limiti e il
10 le conclusioni.
