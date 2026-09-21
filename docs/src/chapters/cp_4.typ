= Scelta del framework

== Criteri e candidati

I criteri per la scelta del framework sono stati fissati prima di guardare i candidati, per evitare di sceglierli in modo
da giustificare una decisione già presa.

Il primo criterio è il costo, che doveva essere nullo trattandosi di un
progetto universitario senza budget. Il secondo è il controllo esplicito sul
flusso, cioè la possibilità di descrivere nel codice l'ordine delle operazioni
invece di lasciarlo emergere dal comportamento del modello. Il terzo è la
capacità di esprimere cicli, dato che sia l'autocorrezione sia la revisione
della risposta sono cicli. Il quarto è il consumo di token, che su un piano
gratuito è una risorsa limitata. Il quinto è la leggibilità dell'architettura,
utile sia durante lo sviluppo sia per questa relazione.

I candidati considerati sono stati quattro. LangGraph descrive il sistema come
un grafo di stati, con nodi e archi dichiarati nel codice. CrewAI organizza il
lavoro fra agenti con ruoli distinti che si passano i risultati. PydanticAI è
più leggero e fornisce output tipizzati, lasciando il ciclo agentico implicito
nel framework. Il Claude Agent SDK mette a disposizione un agente già completo
di strumenti.

#figure(
  table(
    columns: (auto, auto, 1fr, auto),
    align: (left, left, left, left),
    stroke: (x, y) => if y == 0 { (bottom: 0.5pt) } else { none },
    [*Framework*], [*Costo*], [*Cicli e controllo del flusso*], [*Architettura*],
    [LangGraph], [gratuito], [archi condizionali espliciti], [diagrammabile],
    [CrewAI], [gratuito], [solo con le Flows], [implicita],
    [PydanticAI], [gratuito], [da scrivere a mano], [implicita],
    [Claude Agent SDK], [a pagamento], [gestiti dal framework], [implicita],
  ),
  caption: [I framework confrontati sui criteri che si sono rivelati
  discriminanti.],
) <tab:framework>

== La scelta e le esclusioni

La scelta è caduta su LangGraph, per una ragione che riguarda la forma del
problema più che le caratteristiche del framework. Tradurre una domanda in SQL
non è un lavoro da dividere fra competenze diverse, ma un ciclo stretto con una
sola competenza, in cui si guarda lo schema, si scrive una query, la si esegue,
si legge l'errore e si corregge. È quindi un problema di controllo di flusso,
che è esattamente ciò che LangGraph descrive. Il grafo inoltre sa generare il
proprio diagramma, usato come figura nel capitolo 5.

Il Claude Agent SDK è stato escluso perché richiede un'API a pagamento senza
piano gratuito, quindi non rispetta il primo criterio.

CrewAI è stato escluso per il secondo e il quarto. Le Crew descrivono ruoli che
si passano il testimone e non permettono di esprimere una condizione del tipo
esegui, controlla il risultato e poi scegli il passo successivo, che è proprio
il ciclo di autocorrezione. CrewAI mette a disposizione le Flows per colmare
questa mancanza, ma usarle significa ricostruire una macchina a stati sopra
un'astrazione pensata per altro, pagando in più il costo dei ruoli. Ogni
chiamata a un agente CrewAI porta infatti con sé la descrizione del ruolo e
dell'obiettivo, per circa mille token aggiuntivi, che su un piano gratuito da
poche migliaia di token al minuto è un costo rilevante. CrewAI dichiara inoltre
di non supportare Python 3.14, la versione installata sulla macchina di
sviluppo, ma questo è un fatto contingente e non è stato considerato un
argomento.

PydanticAI è stato scartato per il quinto criterio. Avrebbe portato a un
risultato funzionante più in fretta e con meno codice, ma il ciclo agentico
resta nascosto dentro il framework, quindi i due cicli del sistema andrebbero
scritti a mano e l'architettura non sarebbe visibile né diagrammabile.
