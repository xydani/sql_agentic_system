= Limiti

Il sistema funziona solo su SQLite. La lettura dello schema usa le istruzioni
#raw("PRAGMA"), che sono specifiche di quel motore, e l'apertura in sola
lettura sfrutta un parametro della connessione che altri database non hanno.
Portarlo su PostgreSQL o MySQL richiederebbe di riscrivere la lettura dello
schema e di trovare un modo equivalente per impedire le scritture, mentre il
resto dell'architettura resterebbe invariato.

Il database usato per le prove del capitolo 8 è stato costruito da chi ha poi
valutato il sistema, e le difficoltà che contiene sono le stesse che il sistema
sa affrontare. I risultati mostrano quindi che l'agente gestisce correttamente
i casi previsti, non che li gestirebbe su dati raccolti da altri. È il limite
metodologico più serio del lavoro.

Le prove del capitolo 8 sono cinque domande ripetute tre volte, quindi quindici
esecuzioni per sistema. È un campione piccolo. Il risultato dice che su quelle
domande il sistema agentico è stato stabile, ma con tre ripetizioni un
comportamento che fallisce di rado potrebbe non essersi mai presentato. Per una
misura più solida servirebbero più domande e più ripetizioni.

Non è infine gestito il caso di uno schema troppo grande per entrare nel
contesto del modello. Sui database usati la descrizione di tutte le tabelle
occupa poco spazio, ma con centinaia di tabelle l'agente non avrebbe modo di
capire quali siano rilevanti per la domanda, e servirebbe un passo che le
seleziona prima.
