#import "@preview/arkheion:0.1.2": arkheion, arkheion-appendices

#show: arkheion.with(
  title: "Riprogettazione di un sistema text-to-SQL in architettura agentica",
  authors: (
    (name: "Daniele Lurani", email: "60/73/65357", affiliation: "Università degli Studi di Cagliari"),
  ),
  abstract: 
"I sistemi text-to-SQL traducono domande in linguaggio naturale in query eseguibili, ma una query sintatticamente valida può rispondere alla domanda sbagliata senza che il database segnali alcun errore. Questa relazione descrive la trasformazione di una pipeline text-to-SQL in un sistema agentico costruito con LangGraph, nel quale il modello linguistico sceglie da solo quali strumenti usare per leggere lo schema, campionare i dati ed eseguire le query, e sottopone la propria risposta a una verifica prima di restituirla. Un primo tentativo di affidare quella verifica a un secondo modello linguistico è fallito proprio sul caso principale, perché il verificatore non disponeva delle informazioni necessarie per riconoscere l'errore. Il controllo è stato quindi riscritto come regola deterministica dentro gli strumenti, lasciando al modello i soli casi che richiedono interpretazione. Su un database di valutazione con quattro tabelle e circa millecinquecento righe, il sistema agentico ha risposto correttamente in quindici esecuzioni su quindici, contro tre su quindici della pipeline di partenza a parità di modello linguistico.
",
  date: "21 Settembre, 2026",
)
#set cite(style: "chicago-author-date")
#show link: underline

#include "chapters/cp_1_intro.typ"
#include "chapters/cp_2.typ"
#include "chapters/cp_3.typ"
#include "chapters/cp_4.typ"
#include "chapters/cp_5.typ"
#include "chapters/cp_6.typ"
#include "chapters/cp_7.typ"
#include "chapters/cp_8.typ"
#include "chapters/cp_9.typ"
#include "chapters/cp_10.typ"
