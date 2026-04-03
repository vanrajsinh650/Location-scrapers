from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


HEADERS = ["#", "Name", "Phone", "Address", "Rating", "Google Maps Link", "Area"]


def style_header(ws):
    fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    for col in range(1, len(HEADERS) + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")


def auto_width(ws):
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        max_len = max((len(str(c.value or "")) for c in col), default=10)
        ws.column_dimensions[letter].width = min(max_len + 4, 60)


def add_rows(ws, data, start_idx=1):
    for i, item in enumerate(data, start_idx):
        ws.append([
            i,
            item.get("name", ""),
            item.get("phone", ""),
            item.get("address", ""),
            item.get("rating", ""),
            item.get("website", ""),
            item.get("area", ""),
        ])


def save_to_excel(results, filepath):
    wb = Workbook()

    ws = wb.active
    ws.title = "All Results"
    ws.append(HEADERS)
    style_header(ws)
    add_rows(ws, results)
    auto_width(ws)

    by_area = {}
    for r in results:
        by_area.setdefault(r.get("area", "Other"), []).append(r)

    for area, data in by_area.items():
        name = area[:31].replace("/", "-").replace("\\", "-")
        ws2 = wb.create_sheet(title=name)
        ws2.append(HEADERS)
        style_header(ws2)
        add_rows(ws2, data)
        auto_width(ws2)

    wb.save(filepath)
