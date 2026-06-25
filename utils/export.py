import csv
import os
from datetime import datetime

def export_csv(reservasi_list: list, filepath: str = None) -> str:
    """
    Export daftar reservasi ke file CSV.
    Jika filepath tidak diberikan, simpan ke folder Downloads user.
    Return path file yang disimpan.
    """
    if not filepath:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads, exist_ok=True)
        filepath = os.path.join(downloads, f"laporan_reservasi_{ts}.csv")

    fieldnames = [
        "ID", "Ruangan", "Peminjam", "Role",
        "Tanggal", "Jam Mulai", "Jam Selesai",
        "Keperluan", "Status", "Catatan Admin"
    ]

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in reservasi_list:
            ruangan = r.get("ruangan") or {}
            pengguna = r.get("pengguna") or {}
            writer.writerow({
                "ID"           : r.get("id", ""),
                "Ruangan"      : ruangan.get("nama", r.get("ruangan_id", "")),
                "Peminjam"     : pengguna.get("nama", r.get("pengguna_id", "")),
                "Role"         : pengguna.get("role", ""),
                "Tanggal"      : r.get("tanggal", ""),
                "Jam Mulai"    : str(r.get("jam_mulai", ""))[:5],
                "Jam Selesai"  : str(r.get("jam_selesai", ""))[:5],
                "Keperluan"    : r.get("keperluan", ""),
                "Status"       : r.get("status", ""),
                "Catatan Admin": r.get("catatan_admin", ""),
            })

    return filepath


# ──────────────────────────────────────────────────────────────
#  EXPORT PDF
# ──────────────────────────────────────────────────────────────

def export_pdf(reservasi_list: list, filepath: str = None,
               filter_info: str = "") -> str:
    """
    Export daftar reservasi ke file PDF menggunakan reportlab.
    Return path file yang disimpan.
    """
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle,
            Paragraph, Spacer
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        raise ImportError(
            "Library 'reportlab' belum terinstall.\n"
            "Jalankan: pip install reportlab"
        )

    if not filepath:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads, exist_ok=True)
        filepath = os.path.join(downloads, f"laporan_reservasi_{ts}.pdf")

    doc = SimpleDocTemplate(
        filepath,
        pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=16, spaceAfter=6, alignment=TA_CENTER
    )
    sub_style = ParagraphStyle(
        "Sub", parent=styles["Normal"],
        fontSize=9, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=12
    )

    elements = []

    # ── Header ──
    elements.append(Paragraph("Laporan Reservasi Ruangan", title_style))
    ts_human = datetime.now().strftime("%d %B %Y, %H:%M")
    sub_text = f"Dicetak: {ts_human}"
    if filter_info:
        sub_text += f"     |     Filter: {filter_info}"
    elements.append(Paragraph(sub_text, sub_style))
    elements.append(Spacer(1, 0.3*cm))

    # ── Tabel ──
    header = ["No", "Ruangan", "Peminjam", "Role",
              "Tanggal", "Jam", "Keperluan", "Status"]
    data = [header]

    for i, r in enumerate(reservasi_list, start=1):
        ruangan  = r.get("ruangan")  or {}
        pengguna = r.get("pengguna") or {}
        jam = (
            f"{str(r.get('jam_mulai',''))[:5]} – "
            f"{str(r.get('jam_selesai',''))[:5]}"
        )
        keperluan = r.get("keperluan", "")
        if len(keperluan) > 40:
            keperluan = keperluan[:38] + "…"

        data.append([
            str(i),
            ruangan.get("nama",  r.get("ruangan_id",  "")),
            pengguna.get("nama", r.get("pengguna_id", "")),
            pengguna.get("role", ""),
            r.get("tanggal", ""),
            jam,
            keperluan,
            r.get("status", ""),
        ])

    # Lebar kolom (total ± A4 landscape usable width ~25.7 cm)
    col_widths = [1*cm, 4*cm, 4*cm, 2.5*cm, 2.8*cm, 3*cm, 6*cm, 2.4*cm]

    table = Table(data, colWidths=col_widths, repeatRows=1)

    STATUS_COLORS = {
        "Disetujui": colors.HexColor("#d1fae5"),
        "Aktif"    : colors.HexColor("#dbeafe"),
        "Pending"  : colors.HexColor("#fef9c3"),
        "Ditolak"  : colors.HexColor("#fee2e2"),
        "Dibatalkan": colors.HexColor("#f3f4f6"),
        "Selesai"  : colors.HexColor("#e0e7ff"),
    }

    style = TableStyle([
        # Header
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 9),
        ("ALIGN",       (0, 0), (-1, 0), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        # Body
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ])

    # Warnai kolom Status sesuai nilainya
    for row_idx, r in enumerate(reservasi_list, start=1):
        status = r.get("status", "")
        bg = STATUS_COLORS.get(status)
        if bg:
            style.add("BACKGROUND", (7, row_idx), (7, row_idx), bg)

    table.setStyle(style)
    elements.append(table)

    # ── Summary ──
    elements.append(Spacer(1, 0.5*cm))
    total = len(reservasi_list)
    from collections import Counter
    status_count = Counter(r.get("status", "-") for r in reservasi_list)
    summary_parts = [f"Total: <b>{total}</b> reservasi"]
    for st, cnt in sorted(status_count.items()):
        summary_parts.append(f"{st}: {cnt}")
    summary_text = "     |     ".join(summary_parts)
    elements.append(Paragraph(summary_text, styles["Normal"]))

    doc.build(elements)
    return filepath
