= Perché non era un sistema agentico

== Pipeline e agente

Prima di trasformare il sistema è stato necessario stabilire cosa distingue un
agente da una normale sequenza di chiamate. Un sistema viene di solito
considerato agentico quando il modello decide da solo cosa fare, può usare
strumenti per procurarsi le informazioni che gli mancano, sa scomporre un
compito in più passi, valuta il risultato del proprio lavoro e conserva memoria
di quello che è già successo.

Il sistema di partenza non soddisfa nessuno di questi punti. Le decisioni non
le prende il modello, perché la sequenza delle operazioni è scritta in un ciclo
#raw("for") dentro #raw("main.py") e il modello viene chiamato sempre nello
stesso momento per fare sempre la stessa cosa. Non ha inoltre alcuno strumento
a disposizione. Riceve lo schema del database già pronto nel prompt e non può
chiedere altro, quindi non può guardare quali valori contiene davvero una
colonna né eseguire la query per conto suo.

Manca anche la pianificazione, perché ogni domanda produce una query e basta.
Una richiesta come confrontare due gruppi di clienti e commentare la differenza
non è esprimibile, dato che andrebbe divisa in più passi. Manca infine la
memoria, visto che in modalità interattiva ogni domanda crea un oggetto
#raw("NL2SQLAgent") nuovo e una domanda che si riferisce alla precedente non
funziona.

Resta la valutazione del risultato, che nel sistema di partenza riguarda solo
gli errori di esecuzione. È il punto più importante dei cinque e viene ripreso
nel paragrafo successivo.

#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    stroke: (x, y) => if y == 0 { (bottom: 0.5pt) } else { none },
    [*Criterio*], [*Sistema di partenza*],
    [Autonomia nelle decisioni], [la sequenza è fissata in un ciclo #raw("for")],
    [Uso di strumenti], [nessuno, il modello produce solo testo],
    [Pianificazione], [una domanda produce una sola query],
    [Valutazione del risultato], [solo gli errori di esecuzione],
    [Memoria], [ogni domanda crea un agente nuovo],
  ),
  caption: [I criteri di agenticità applicati al sistema di partenza.],
) <tab:criteri>

== Successo non vuol dire correttezza

Il campo #raw("result.success") vale vero quando SQLite ha eseguito la query
senza sollevare eccezioni. Non dice però niente sul fatto che la query risponda
alla domanda posta. Una query con la join sbagliata, con #raw("COUNT") al posto
di #raw("SUM") o con un filtro dimenticato viene eseguita senza problemi e
considerata un successo.

Il caso più chiaro riguarda i valori contenuti nelle colonne. Nel database di
esempio la colonna #raw("country") contiene codici come #raw("IT") e
#raw("UK"), non i nomi estesi dei paesi. Alla domanda su quanti siano i clienti
italiani il modello scrive #raw("WHERE country = 'Italy'"), perché è la
scrittura più naturale e nulla nello schema lo avverte del contrario. La query
viene eseguita, restituisce zero righe e il sistema la considera riuscita. La
risposta è zero ed è sbagliata.

Il meccanismo di autocorrezione descritto nel capitolo precedente non può
intervenire, perché non c'è nessun errore da rimandare al modello. Questo è il
problema da cui è partita la riprogettazione, e viene ripreso nel capitolo 7.
