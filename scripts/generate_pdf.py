#!/usr/bin/env python3
"""Generatore di schede palestra PDF a partire da un programma JSON.

Uso:
    python generate_pdf.py <programma.json> <output.pdf> [--kb references/knowledge_base.json]
    python generate_pdf.py --selftest

Il programma JSON descrive utente/obiettivo/giorni/esercizi (vedi examples/scheda_esempio.json).
Ogni esercizio viene validato contro la knowledge base: se il nome non e' presente
(match case-insensitive per sottostringa), viene marcato con un avviso "[?]" nel PDF
e stampato un warning su stderr, senza inventare dati mancanti.
"""
import sys
import os
import json
import argparse
import urllib.parse

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)

PRIMARY = colors.HexColor("#1E1B4B")
ACCENT = colors.HexColor("#4F46E5")
DARK_BG = colors.HexColor("#0F172A")
LIGHT_BG = colors.HexColor("#F8FAFC")
CARD_BG = colors.HexColor("#F1F5F9")
HEAVY_RED = colors.HexColor("#991B1B")
HYPER_BLUE = colors.HexColor("#3730A3")
ISO_AMBER = colors.HexColor("#92400E")
TEXT_DARK = colors.HexColor("#1E293B")
TEXT_MUTED = colors.HexColor("#64748B")
WARN_RED = colors.HexColor("#B91C1C")

BADGE_COLOR = {"HEAVY": HEAVY_RED, "HYPER": HYPER_BLUE, "ISO": ISO_AMBER}

STYLES = {
    "title": ParagraphStyle("DocTitle", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=colors.white),
    "subtitle": ParagraphStyle("DocSubTitle", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=colors.HexColor("#A5B4FC")),
    "meta": ParagraphStyle("MetaText", fontName="Helvetica", fontSize=8, leading=11, textColor=colors.HexColor("#CBD5E1")),
    "section": ParagraphStyle("SectionHeading", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=PRIMARY, spaceBefore=8, spaceAfter=4),
    "body": ParagraphStyle("BodyTextCustom", fontName="Helvetica", fontSize=8, leading=11, textColor=TEXT_DARK),
    "th": ParagraphStyle("TableHeader", fontName="Helvetica-Bold", fontSize=7, leading=9, textColor=colors.white, alignment=1),
    "td": ParagraphStyle("TableCell", fontName="Helvetica", fontSize=7.5, leading=10, textColor=TEXT_DARK),
    "td_bold": ParagraphStyle("TableCellBold", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=TEXT_DARK),
    "td_sub": ParagraphStyle("TableCellSub", fontName="Helvetica-Oblique", fontSize=6.5, leading=8, textColor=TEXT_MUTED),
    "badge": lambda color: ParagraphStyle(f"Badge{color}", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=color, alignment=1),
}


def load_json(path):
    if not os.path.isfile(path):
        raise SystemExit(f"Errore: file non trovato: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_kb(kb_path):
    if not kb_path or not os.path.isfile(kb_path):
        return None
    return load_json(kb_path)


def kb_exercise_names(kb):
    if not kb:
        return set()
    return {e["nome"].strip().lower() for e in kb.get("esercizi", [])}


def validate_program(program, kb):
    """Ritorna lista di warning per esercizi non presenti nella KB."""
    warnings = []
    known = kb_exercise_names(kb)
    if not known:
        return warnings
    for day in program.get("giorni", []):
        for ex in day.get("esercizi", []):
            nome = ex.get("nome", "").strip().lower()
            if not any(nome in k or k in nome for k in known):
                warnings.append(f"Esercizio non trovato in knowledge_base.json: '{ex.get('nome')}'")
    return warnings


def yt_link(search_term):
    encoded = urllib.parse.quote(f"{search_term} esecuzione")
    return f"https://www.youtube.com/results?search_query={encoded}"


def exercise_header(nome, search_term, in_kb):
    label = nome if in_kb else f"{nome} [?]"
    color = "#0F172A" if in_kb else "#B91C1C"
    badge = ""
    if search_term:
        url = yt_link(search_term)
        badge = f"&nbsp;<a href='{url}'><font color='#DC2626' size='7'><b>[&#9654; YouTube]</b></font></a>"
    return f"<font color='{color}'><b>{label}</b></font>{badge}"


def header_block(meta):
    rows = [
        [Paragraph(meta.get("titolo_programma", "SCHEDA ALLENAMENTO"), STYLES["title"])],
        [Paragraph(meta.get("sottotitolo", ""), STYLES["subtitle"])],
        [Paragraph(
            f"<b>Atleta:</b> {meta.get('utente', '-')} &nbsp;|&nbsp; "
            f"<b>Obiettivo:</b> {meta.get('obiettivo', '-')} &nbsp;|&nbsp; "
            f"<b>Livello:</b> {meta.get('livello', '-')} &nbsp;|&nbsp; "
            f"<b>Data:</b> {meta.get('data', '-')} &nbsp;|&nbsp; "
            f"<b>{meta.get('settimana', '')}</b>",
            STYLES["meta"]
        )]
    ]
    table = Table(rows, colWidths=[190 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BG),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, colors.HexColor("#334155")),
    ]))
    return table


def bullet_list_box(title, items):
    if not items:
        return None
    body = f"<b>{title}</b><br/>" + "<br/>".join(f"&bull; {i}" for i in items)
    p = Paragraph(body, STYLES["body"])
    box = Table([[p]], colWidths=[190 * mm])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    return box


def exercise_table(esercizi, known_names):
    col_widths = [7 * mm, 68 * mm, 14 * mm, 10 * mm, 16 * mm, 22 * mm, 17 * mm, 20 * mm, 26 * mm]
    headers = [Paragraph(h, STYLES["th"]) for h in
               ["#", "Esercizio & Target", "Tipo", "Serie", "Rip", "RIR/RPE", "Rest", "Tempo", "Note"]]
    rows = [headers]
    for i, ex in enumerate(esercizi, start=1):
        nome = ex.get("nome", "")
        in_kb = (not known_names) or any(nome.strip().lower() in k or k in nome.strip().lower() for k in known_names)
        tipo = ex.get("tipo", "")
        badge_color = BADGE_COLOR.get(tipo, TEXT_MUTED)
        rows.append([
            Paragraph(f"<b>{i}</b>", STYLES["td_bold"]),
            Paragraph(
                f"{exercise_header(nome, ex.get('search_term'), in_kb)}<br/>"
                f"<font color='#64748B'>{ex.get('target', '')}</font>",
                STYLES["td"]
            ),
            Paragraph(tipo, STYLES["badge"](badge_color)),
            Paragraph(str(ex.get("serie", "-")), STYLES["td_bold"]),
            Paragraph(str(ex.get("ripetizioni", "-")), STYLES["td_bold"]),
            Paragraph(str(ex.get("rir", "-")), STYLES["td"]),
            Paragraph(str(ex.get("recupero", "-")), STYLES["td"]),
            Paragraph(str(ex.get("tempo", "-")), STYLES["td"]),
            Paragraph(ex.get("note", "-"), STYLES["td_sub"]),
        ])
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (2, 1), (7, -1), "CENTER"),
    ]))
    return table


def build_pdf(program, kb, output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=10 * mm, rightMargin=10 * mm, topMargin=10 * mm, bottomMargin=10 * mm
    )
    known_names = kb_exercise_names(kb)
    story = [header_block(program), Spacer(1, 4 * mm)]

    wu = bullet_list_box("Riscaldamento", program.get("riscaldamento", []))
    if wu:
        story += [Paragraph("Riscaldamento", STYLES["section"]),
                   HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=4), wu, Spacer(1, 4 * mm)]

    for idx, day in enumerate(program.get("giorni", []), start=1):
        story.append(Paragraph(day.get("titolo", f"Giorno {idx}"), STYLES["section"]))
        story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=4))
        story.append(exercise_table(day.get("esercizi", []), known_names))
        if day.get("note"):
            note_box = Table([[Paragraph(f"<b>Note tecniche:</b> {day['note']}", STYLES["td_sub"])]],
                              colWidths=[190 * mm])
            note_box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(Spacer(1, 2 * mm))
            story.append(note_box)
        story.append(Spacer(1, 4 * mm))
        if idx < len(program.get("giorni", [])):
            story.append(PageBreak())

    cd = bullet_list_box("Defaticamento / Stretching", program.get("defaticamento", []))
    if cd:
        story += [cd, Spacer(1, 4 * mm)]

    default_sicurezza = "Interrompere l'esercizio in caso di dolore acuto, mantenere tecnica prima del carico."
    default_progressione = "Doppia progressione: a parita' di RIR target, aumenta le reps fino al limite superiore del range poi incrementa il carico."
    footer_text = (
        f"<b>Note di sicurezza:</b> {program.get('note_sicurezza', default_sicurezza)}<br/>"
        f"<b>Progressione:</b> {program.get('note_progressione', default_progressione)}"
    )
    story.append(Paragraph(footer_text, STYLES["td_sub"]))

    doc.build(story)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Genera una scheda palestra PDF da un programma JSON.")
    parser.add_argument("programma", nargs="?", help="Percorso al file JSON del programma")
    parser.add_argument("output", nargs="?", help="Percorso del PDF di output")
    parser.add_argument("--kb", default=os.path.join(os.path.dirname(__file__), "..", "references", "knowledge_base.json"),
                         help="Percorso alla knowledge base JSON (default: references/knowledge_base.json)")
    parser.add_argument("--selftest", action="store_true", help="Esegue un self-check e termina")
    args = parser.parse_args()

    if args.selftest:
        selftest()
        return

    if not args.programma or not args.output:
        parser.error("servono <programma.json> e <output.pdf> (oppure --selftest)")

    program = load_json(args.programma)
    kb = load_kb(args.kb)
    if kb is None:
        print(f"Warning: knowledge base non trovata in {args.kb}, salto la validazione.", file=sys.stderr)

    for w in validate_program(program, kb):
        print(f"Warning: {w}", file=sys.stderr)

    build_pdf(program, kb, args.output)
    print(f"PDF generato: {args.output}")


def selftest():
    """python generate_pdf.py --selftest: verifica validazione + generazione PDF minimi."""
    import tempfile

    kb = {"esercizi": [{"nome": "Squat con Bilanciere (Back Squat)"}]}
    program_ok = {"utente": "Test", "obiettivo": "Ipertrofia", "giorni": [
        {"titolo": "Giorno A", "esercizi": [{"nome": "Squat con Bilanciere", "tipo": "HEAVY", "serie": 4, "ripetizioni": "3-5"}]}
    ]}
    program_bad = {"utente": "Test", "giorni": [
        {"titolo": "Giorno A", "esercizi": [{"nome": "Esercizio Inesistente Xyz", "tipo": "HEAVY"}]}
    ]}

    assert validate_program(program_ok, kb) == [], "esercizio noto non deve generare warning"
    warns = validate_program(program_bad, kb)
    assert len(warns) == 1, "esercizio sconosciuto deve generare esattamente 1 warning"

    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "test.pdf")
        build_pdf(program_ok, kb, out)
        assert os.path.isfile(out) and os.path.getsize(out) > 0, "il PDF deve essere creato e non vuoto"

    print("Selftest OK: validazione e generazione PDF funzionano correttamente.")


if __name__ == "__main__":
    main()
