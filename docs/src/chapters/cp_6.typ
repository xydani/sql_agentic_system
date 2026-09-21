= Implementazione

== Organizzazione del codice

Il progetto è diviso in due pacchetti. In #raw("sql_agent") sta il sistema
agentico, con la scelta del modello, gli strumenti, il grafo e le funzioni che
leggono ed eseguono sul database. In #raw("legacy") è conservato il sistema di
partenza, che serve da termine di paragone per il confronto del capitolo 8. La
separazione rende immediato distinguere cosa è stato scritto da cosa era già
presente.

Buona parte del codice del sistema di partenza è stata riusata. Gli strumenti
dell'agente non fanno altro che richiamare le funzioni di introspezione dello
schema e di esecuzione che esistevano già. È stata mantenuta anche l'esecuzione
in sottoprocesso, che era una scelta corretta, perché una query che si blocca
viene interrotta con un timeout senza fermare il ciclo dell'agente.

Il modello linguistico non è fissato nel codice ma scelto da una variabile
d'ambiente, fra due fornitori che offrono entrambi un piano gratuito. La
ragione non è la flessibilità in sé, ma il fatto che i piani gratuiti limitano
i token al minuto, e restare senza quota durante una dimostrazione bloccherebbe
il sistema. Entrambi i fornitori sono stati provati sulle stesse domande.

== Il controllo sulle scritture

Nel sistema di partenza le query venivano scritte da un modello chiamato una
volta sola e passavano per un ciclo esterno. Ora è l'agente a decidere da solo
quando eseguire una query, e può farlo più volte per ogni domanda, quindi il
controllo su cosa viene eseguito diventa più importante. Il controllo è stato
riscritto su tre strati, perché nessun controllo singolo è sufficiente.

#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    stroke: (x, y) => if y == 0 { (bottom: 0.5pt) } else { none },
    [*Strato*], [*Cosa ferma*],
    [Apertura in sola lettura],
    [ogni scrittura, rifiutata direttamente da SQLite],
    [Lista dei comandi permessi],
    [tutto ciò che non inizia con #raw("SELECT") o #raw("WITH"), dopo aver
    tolto commenti e stringhe],
    [Controllo sul resto della query],
    [più istruzioni separate da punto e virgola, e scritture nascoste dopo un
    #raw("WITH")],
  ),
  caption: [I tre strati del controllo sulle query.],
) <tab:strati>

La differenza principale rispetto al sistema di partenza è che il secondo
strato elenca ciò che è permesso invece di ciò che è vietato. Una lista di
divieti è incompleta per costruzione, perché ogni comando che non viene in
mente resta permesso, ed è esattamente quello che succedeva prima con
#raw("CREATE") e #raw("ATTACH"). Una lista di permessi rifiuta invece per
default tutto ciò che non riconosce.

I commenti e le stringhe vengono tolti prima di guardare la prima parola,
altrimenti basterebbe un commento iniziale per nascondere un comando di
scrittura. Allo stesso tempo il controllo non guarda mai il testo intero della
query, così una parola come #raw("DROP") scritta dentro una stringa o una
colonna chiamata #raw("updated_at") non vengono scambiate per scritture.

Un ultimo accorgimento riguarda il numero di righe restituite. Le query vengono
troncate a un massimo e il risultato porta con sé l'indicazione di essere stato
troncato, così l'agente sa di guardare un campione e non ne conta le righe come
se fossero il totale.
