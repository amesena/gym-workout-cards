# gym-workout-cards

Agent Skill per generare **schede palestra (workout card) in PDF** evidence-based,
a partire da una knowledge base scientifica di esercizi (Delavier, Schoenfeld,
Helms/NSCA). L'agente raccoglie obiettivo, livello, giorni/settimana, split,
attrezzatura e limitazioni dell'utente, seleziona gli esercizi **solo** dalla
knowledge base fornita e produce un PDF A4 stampabile con riscaldamento,
blocco principale (serie x ripetizioni, RIR/RPE, recupero, tempo, note) e
defaticamento. Prima di generare qualsiasi scheda, l'agente pone sempre
all'utente un questionario di raccolta requisiti (obiettivo, livello, giorni,
split, attrezzatura, infortuni/limitazioni, durata sessione).

## Cosa contiene

```
gym-workout-cards/
├─ SKILL.md                          # definizione skill (frontmatter + workflow)
├─ scripts/generate_pdf.py           # generatore PDF (Python + reportlab)
├─ references/knowledge_base.json    # esercizi + regole scientifiche (fonte per l'agente)
├─ references/sources/                # estratto testi originali (Delavier/Schoenfeld/Helms/NSCA) a corredo
├─ templates/scheda_template.html    # layout HTML di riferimento
├─ examples/scheda_esempio.json      # programma di esempio (Upper/Lower)
├─ examples/scheda_esempio.pdf       # PDF generato dall'esempio
└─ LICENSE
```

## Installazione

Con [`npx skills`](https://github.com/vercel-labs/skills):

```bash
npx skills add amesena/gym-workout-cards
```

Per installarla solo su un agente specifico (es. Claude Code):

```bash
npx skills add amesena/gym-workout-cards -a claude-code
```

### Dipendenze dello script

```bash
pip install reportlab
```

## Uso

Una volta installata, chiedi semplicemente al tuo agente:

> "Crea una scheda palestra per ipertrofia, livello intermedio, 4 giorni a
> settimana, split upper/lower, palestra completa, nessun infortunio."

L'agente:
1. pone il questionario di raccolta requisiti e attende le risposte;
2. seleziona gli esercizi da `references/knowledge_base.json`;
3. compone il programma come JSON;
4. genera il PDF con:
   ```bash
   python scripts/generate_pdf.py programma.json scheda.pdf --kb references/knowledge_base.json
   ```

Puoi anche generare direttamente l'esempio incluso:

```bash
python scripts/generate_pdf.py examples/scheda_esempio.json output.pdf --kb references/knowledge_base.json
```

Per verificare che lo script funzioni correttamente nel tuo ambiente:

```bash
python scripts/generate_pdf.py --selftest
```

## Note

- Lo script **non inventa esercizi**: se un nome esercizio nel programma non è
  presente in `knowledge_base.json`, viene marcato `[?]` in rosso nel PDF e
  segnalato come warning su stderr.
- `templates/scheda_template.html` documenta lo stesso schema dati in un
  layout HTML, utile come riferimento visuale o per un flusso HTML→PDF
  alternativo (es. weasyprint) senza modificare `generate_pdf.py`.

## Licenza

MIT — vedi [LICENSE](LICENSE).
