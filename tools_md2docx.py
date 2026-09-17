"""Chuyen DAC_TA_YEU_CAU.md sang .docx, giu bang bieu va anh so do."""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

NGUON = [Path(p) for p in sys.argv[1:-1]]      # mot hoac nhieu file .md
OUT = Path(sys.argv[-1])

FONT = "Times New Roman"
XANH = RGBColor(0x1F, 0x3B, 0x63)

# **dam** | `ma` | [chu](link) | *nghieng*
INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|\*[^*\s][^*]*\*)")


def dat_font(run, ten=FONT):
    run.font.name = ten
    run._element.rPr.rFonts.set(qn("w:eastAsia"), ten)


def viet_inline(para, text, dam_san=False, co_chu=13):
    """Tach chuoi thanh cac run co dinh dang; tra ve so run da them."""
    for phan in INLINE.split(text):
        if not phan:
            continue
        dam, nghieng, ma = dam_san, False, False
        if phan.startswith("**") and phan.endswith("**"):
            phan, dam = phan[2:-2], True
        elif phan.startswith("`") and phan.endswith("`"):
            phan, ma = phan[1:-1], True
        elif phan.startswith("[") and "](" in phan:
            phan = phan[1:phan.index("](")]          # giu chu, bo dia chi
        elif phan.startswith("*") and phan.endswith("*") and len(phan) > 2:
            phan, nghieng = phan[1:-1], True
        r = para.add_run(phan)
        r.bold, r.italic = dam, nghieng
        r.font.size = Pt(co_chu - 1 if ma else co_chu)
        dat_font(r, "Consolas" if ma else FONT)


def tach_hang(dong):
    """| a | b | -> ['a', 'b']"""
    return [o.strip() for o in dong.strip().strip("|").split("|")]


def them_bang(doc, hang_ds):
    dau = tach_hang(hang_ds[0])
    than = [tach_hang(h) for h in hang_ds[2:]]
    t = doc.add_table(rows=1, cols=len(dau))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, o in enumerate(dau):
        p = t.rows[0].cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        viet_inline(p, o, dam_san=True, co_chu=11)
    for hang in than:
        o_ds = t.add_row().cells
        for i, o in enumerate(hang[:len(dau)]):
            # <br> trong o -> nhieu doan
            for j, doan in enumerate(o.split("<br>")):
                p = o_ds[i].paragraphs[0] if j == 0 else o_ds[i].add_paragraph()
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                viet_inline(p, doan.strip(), co_chu=11)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def chay():
    doc = Document()

    s = doc.sections[0]
    s.top_margin, s.bottom_margin = Cm(2), Cm(2)
    s.left_margin, s.right_margin = Cm(3), Cm(2)

    n = doc.styles["Normal"]
    n.font.name, n.font.size = FONT, Pt(13)
    n.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    n.paragraph_format.line_spacing = 1.4
    n.paragraph_format.space_after = Pt(6)

    for muc, co in (("Heading 1", 17), ("Heading 2", 15), ("Heading 3", 13.5),
                    ("Heading 4", 13)):
        st = doc.styles[muc]
        st.font.name, st.font.size = FONT, Pt(co)
        st.font.color.rgb, st.font.bold = XANH, True
        st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    for k, src in enumerate(NGUON):
        if k:                                     # moi tai lieu bat dau trang moi
            doc.add_page_break()
        nap(doc, src)

    doc.save(OUT)
    print(f"Da ghi {OUT} ({OUT.stat().st_size // 1024} KB)"
          f" tu {len(NGUON)} nguon")


def nap(doc, src):
    BASE = src.parent
    dong_ds = src.read_text(encoding="utf-8").split("\n")
    i = 0
    while i < len(dong_ds):
        d = dong_ds[i]
        cat = d.strip()

        if not cat or cat == "---":
            i += 1
            continue

        if cat.startswith("|") and i + 1 < len(dong_ds) and set(
                dong_ds[i + 1].strip()) <= set("|-: "):
            khoi = []
            while i < len(dong_ds) and dong_ds[i].strip().startswith("|"):
                khoi.append(dong_ds[i])
                i += 1
            them_bang(doc, khoi)
            continue

        if cat.startswith("!["):                      # anh
            duong = cat[cat.index("](") + 2:cat.rindex(")")]
            tep = BASE / duong
            if tep.is_file():
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.add_run().add_picture(str(tep), width=Cm(16))
            i += 1
            continue

        if cat.startswith("#"):
            bac = len(cat) - len(cat.lstrip("#"))
            doc.add_heading(cat.lstrip("# ").strip(), level=min(bac, 4))
            i += 1
            continue

        if cat.startswith(("- ", "* ")):
            p = doc.add_paragraph(style="List Bullet")
            viet_inline(p, cat[2:])
            i += 1
            continue

        if re.match(r"^\d+\.\s", cat):
            p = doc.add_paragraph(style="List Number")
            viet_inline(p, re.sub(r"^\d+\.\s", "", cat))
            i += 1
            continue

        if cat.startswith(">"):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1)
            viet_inline(p, cat.lstrip("> ").strip())
            for r in p.runs:
                r.italic = True
            i += 1
            continue

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        viet_inline(p, cat)
        i += 1


chay()
