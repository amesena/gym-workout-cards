---
name: gym-workout-cards
description: >-
  Genera schede palestra (workout card) in PDF a partire da una knowledge base
  scientifica di esercizi (references/knowledge_base.json): raccoglie obiettivo,
  livello, giorni/settimana, split, attrezzatura e limitazioni dell'utente,
  seleziona esercizi SOLO dalla knowledge base e produce un PDF A4 stampabile
  con riscaldamento, blocco principale (serie x ripetizioni, RIR/RPE, recupero,
  tempo, note) e defaticamento. Prima di generare la scheda pone sempre
  all'utente un questionario di raccolta requisiti. Usa questa
  skill quando l'utente chiede una "scheda palestra", "workout card", "programma
  allenamento", "scheda di allenamento", un "PDF palestra" o vuole pianificare
  ipertrofia, forza, dimagrimento o ricomposizione corporea (full body,
  upper/lower, push-pull-legs, ecc.). In inglese: "gym workout card", "workout
  program PDF", "training plan", "generate a workout sheet".
---

# Gym Workout Cards

Genera schede palestra in PDF, evidence-based, usando **solo** gli esercizi e le
regole contenute in `references/knowledge_base.json`. Non inventare esercizi,
carichi o regole non presenti nella knowledge base: se qualcosa manca, va
segnalato esplicitamente all'utente.

## When to Use

Attiva questa skill quando l'utente chiede di:
- creare/generare una "scheda palestra", "workout card", "programma di
  allenamento", "scheda di allenamento", un "PDF palestra";
- pianificare un mesociclo/settimana di allenamento per ipertrofia, forza,
  dimagrimento o ricomposizione corporea;
- aggiornare/adattare una scheda esistente (nuova settimana, progressione,
  cambio split, infortunio da gestire).

Non usarla per domande puramente teoriche sulla scienza dell'allenamento senza
richiesta di output (in quel caso rispondi direttamente dalle pagine in
`concepts/` del vault, se disponibili).

## Steps

1. **Poni sempre il questionario di raccolta requisiti prima di procedere.**
   Non generare mai una scheda al primo messaggio, anche se l'utente sembra
   aver già fornito alcune informazioni: fai le domande sotto (una singola
   volta, raggruppate) e aspetta la risposta prima di leggere la knowledge
   base o comporre il programma. Domande obbligatorie:
   - Obiettivo: ipertrofia / forza / dimagrimento / ricomposizione
   - Livello: principiante / intermedio / avanzato
   - Giorni di allenamento a settimana
   - Tipo di split: full body, upper/lower, push-pull-legs, o "suggerisci tu"
   - Attrezzatura disponibile (palestra completa, casa con manubri, solo corpo
     libero, ecc.)
   - Limitazioni/infortuni (spalla, lombare, ginocchio, gomito/polso, nessuna)
   - Durata sessione desiderata
   - Nome utente, data, settimana/mesociclo (per l'intestazione)
   Se l'utente ha già anticipato una o più risposte nel messaggio iniziale,
   confermale invece di richiederle, ma chiedi comunque quelle mancanti: non
   procedere con la generazione finché tutti i punti sopra non sono coperti
   (specialmente infortuni/limitazioni, per motivi di sicurezza).

2. **Leggi `references/knowledge_base.json`.** Contiene:
   - `principi`: piramide di Helms, scala RIR/RPE, volume settimanale per
     gruppo muscolare, frequenza, recuperi per categoria, tempo di esecuzione,
     modelli di progressione per livello, controindicazioni generali per zona
     infortunio.
   - `esercizi`: lista di esercizi con `gruppo_muscolare`, `target`,
     `categoria` (multiarticolare/isolamento), `tag_intensita`
     (HEAVY/HYPER/ISO), `attrezzatura`, range di `serie`/`ripetizioni`, `rir`,
     `recupero`, `tempo`, `note_tecniche`, `controindicazioni`, `search_term`.
   - `riscaldamento_pool` / `defaticamento_pool`: blocchi pronti per apertura
     e chiusura seduta.

3. **Seleziona esercizi SOLO da `esercizi`**, filtrando per:
   - attrezzatura disponibile (campo `attrezzatura`);
   - `controindicazioni` che intersecano le limitazioni dichiarate dall'utente
     → escludi quell'esercizio e proponi l'alternativa indicata in
     `principi.controindicazioni_generali`;
   - split scelto: distribuisci i `gruppo_muscolare` sui giorni (es. full body
     = tutti i gruppi ogni giorno con meno esercizi ciascuno; upper/lower =
     Petto/Dorso/Spalle/Braccia vs Gambe/Core; PPL = spinta/trazione/gambe).
   - Se un esercizio richiesto esplicitamente dall'utente NON è nella
     knowledge base, dillo chiaramente e proponi il più vicino disponibile
     invece di inventarlo.

4. **Applica le regole di `principi`** per compilare ogni riga:
   - Serie/ripetizioni/RIR dal record esercizio (adatta leggermente in base a
     obiettivo: forza → più vicino a HEAVY con rep basse, ipertrofia → mix
     HYPER/ISO, dimagrimento → volume moderato + recuperi più corti se
     compatibile, mantenendo comunque i range della KB).
   - Recupero e tempo di esecuzione da `principi.recuperi_per_categoria` /
     `principi.tempo_esecuzione` se il record esercizio non lo specifica.
   - Modello di progressione da `principi.progressione` in base al livello
     dichiarato, da inserire in `note_progressione`.
   - Volume settimanale per gruppo muscolare entro 10-20 serie
     (`principi.volume_settimanale_per_gruppo`), verificando che la somma
     delle serie sui giorni non superi la soglia MRV per un dato gruppo.

5. **Componi il programma come oggetto JSON** con questa struttura (vedi
   `examples/scheda_esempio.json` per un esempio completo):
   ```json
   {
     "titolo_programma": "...", "sottotitolo": "...",
     "utente": "...", "obiettivo": "...", "livello": "...",
     "data": "...", "settimana": "...",
     "riscaldamento": ["...", "..."],
     "giorni": [
       {"titolo": "Giorno A - ...", "esercizi": [
         {"nome": "...", "target": "...", "tipo": "HEAVY|HYPER|ISO",
          "serie": 4, "ripetizioni": "3-5", "rir": "1-2 RIR (RPE 8-9)",
          "recupero": "3.0 min", "tempo": "2-0-X-0", "note": "...",
          "search_term": "..."}
       ], "note": "note biomeccaniche del giorno"}
     ],
     "defaticamento": ["...", "..."],
     "note_sicurezza": "...",
     "note_progressione": "..."
   }
   ```
   Salva questo file (es. in una cartella di lavoro temporanea o su richiesta
   dell'utente).

6. **Genera il PDF** eseguendo lo script:
   ```bash
   python scripts/generate_pdf.py <percorso_programma.json> <percorso_output.pdf> --kb references/knowledge_base.json
   ```
   Lo script:
   - valida ogni esercizio contro la knowledge base e stampa un `Warning:` su
     stderr per ogni esercizio non trovato (marcandolo anche nel PDF con
     `[?]` in rosso, senza bloccare la generazione);
   - produce un PDF A4 con intestazione (utente, obiettivo, livello, data,
     settimana), tabelle per ogni giorno (esercizio, tipo, serie, rip,
     RIR/RPE, recupero, tempo, note), sezioni riscaldamento/defaticamento e
     footer con note di sicurezza e progressione.
   - se lo script segnala warning, riportali all'utente prima di consegnare il
     PDF.

7. **Consegna il risultato**: indica il percorso del PDF generato e riassumi
   in breve split, volume settimanale per gruppo e la regola di progressione
   applicata. Se ci sono stati esercizi non trovati in KB o gruppi muscolari
   sotto/sopra il volume raccomandato, segnalalo esplicitamente.

## Gestione errori

- **Input mancanti** (obiettivo, livello, giorni/settimana, attrezzatura): non
  procedere con la generazione, chiedi all'utente i dati minimi mancanti.
- **Esercizio richiesto non in knowledge base**: non inventarlo. Segnalalo e
  suggerisci l'esercizio più simile presente in `esercizi` per lo stesso
  `gruppo_muscolare`.
- **Attrezzatura assente per un esercizio necessario**: filtra `esercizi` per
  `attrezzatura` compatibile con quanto dichiarato dall'utente; se nessun
  esercizio della KB copre un gruppo muscolare con l'attrezzatura disponibile,
  dillo esplicitamente invece di forzare una scelta incompatibile.
- **Limitazioni/infortuni dichiarati**: escludi ogni esercizio la cui lista
  `controindicazioni` include la zona indicata e usa
  `principi.controindicazioni_generali` per proporre l'alternativa a basso
  stress su quella zona.
- **Script che fallisce** (file JSON non trovato, JSON malformato): lo script
  termina con un messaggio d'errore chiaro (`Errore: file non trovato: ...`);
  correggi il percorso o la sintassi JSON e riprova.

## File della skill

- `references/knowledge_base.json` — knowledge base **strutturata** di
  esercizi e regole (distillata da Delavier, Schoenfeld, Helms, NSCA). Unica
  fonte ammessa per la selezione esercizi e per compilare serie/rip/RIR/
  recupero/tempo/progressione.
- `references/sources/` — testo originale delle pagine da cui è stata
  distillata `knowledge_base.json` (concetti Helms/Schoenfeld su piramide,
  volume, RIR/RPE, tempo, progressione, selezione esercizi, recupero,
  frequenza, aderenza; profili degli autori; schede dei 4 libri fonte). Usa
  questi file solo per citare/motivare una scelta con maggior dettaglio
  all'utente — non contengono dati aggiuntivi di esercizi oltre a quelli già
  in `knowledge_base.json`, e i wikilink `[[...]]` al loro interno puntano al
  vault originale (non risolvibili fuori da esso, è un estratto).
- `scripts/generate_pdf.py` — genera il PDF con reportlab a partire da un
  programma JSON; supporta `--selftest` per un check rapido di funzionamento.
- `templates/scheda_template.html` — layout HTML di riferimento (stessa
  struttura dati) utile come alternativa visuale o per chi preferisce un
  flusso HTML → PDF manuale.
- `examples/scheda_esempio.json` + `examples/scheda_esempio.pdf` — esempio
  completo di programma Upper/Lower per ipertrofia intermedio, con relativo
  PDF generato.
