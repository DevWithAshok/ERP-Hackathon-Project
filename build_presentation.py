from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "presentation_assets"
OUTPUT = ROOT / "Manufacturing_ERP_Demo.pptx"

NAVY = RGBColor(23, 32, 51)
BLUE = RGBColor(23, 105, 170)
MUTED = RGBColor(102, 116, 133)
LIGHT = RGBColor(244, 247, 251)
WHITE = RGBColor(255, 255, 255)
GREEN = RGBColor(6, 118, 71)
RED = RGBColor(180, 35, 24)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]


def add_background(slide, color=LIGHT):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_title(slide, title, subtitle=None):
    box = slide.shapes.add_textbox(Inches(0.55), Inches(0.3), Inches(12.2), Inches(0.7))
    text = box.text_frame
    text.clear()
    p = text.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = NAVY
    if subtitle:
        sub = slide.shapes.add_textbox(Inches(0.58), Inches(0.92), Inches(12), Inches(0.4))
        p = sub.text_frame.paragraphs[0]
        p.text = subtitle
        p.font.size = Pt(12)
        p.font.color.rgb = MUTED


def add_footer(slide, number):
    line = slide.shapes.add_shape(1, Inches(0.55), Inches(7.12), Inches(12.2), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = RGBColor(217, 226, 236)
    line.line.fill.background()
    box = slide.shapes.add_textbox(Inches(11.9), Inches(7.18), Inches(0.8), Inches(0.2))
    p = box.text_frame.paragraphs[0]
    p.text = str(number)
    p.alignment = PP_ALIGN.RIGHT
    p.font.size = Pt(9)
    p.font.color.rgb = MUTED


def add_bullets(slide, items, x, y, w, h, size=18, color=NAVY):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    frame.clear()
    for index, item in enumerate(items):
        p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        p.text = item
        p.level = 0
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.space_after = Pt(9)
        p.text = "• " + p.text
    return box


def add_image(slide, filename, x, y, w, h):
    path = ASSETS / filename
    if path.exists():
        slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w), height=Inches(h))
    else:
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        p = box.text_frame.paragraphs[0]
        p.text = f"Screenshot unavailable: {filename}"
        p.font.size = Pt(14)
        p.font.color.rgb = RED


def add_label(slide, text, x, y, w):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(0.3))
    p = box.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = BLUE


# 1. Title
slide = prs.slides.add_slide(blank)
add_background(slide, NAVY)
box = slide.shapes.add_textbox(Inches(0.8), Inches(1.55), Inches(11.8), Inches(1.2))
p = box.text_frame.paragraphs[0]
p.text = "Manufacturing ERP System"
p.font.size = Pt(42)
p.font.bold = True
p.font.color.rgb = WHITE
sub = slide.shapes.add_textbox(Inches(0.85), Inches(3.0), Inches(10.8), Inches(1.1))
p = sub.text_frame.paragraphs[0]
p.text = "A connected system for products, inventory, purchasing, production, customers, sales, and reports"
p.font.size = Pt(22)
p.font.color.rgb = RGBColor(211, 229, 244)
foot = slide.shapes.add_textbox(Inches(0.85), Inches(6.3), Inches(10), Inches(0.4))
p = foot.text_frame.paragraphs[0]
p.text = "MWS TECHSPRINT 2026 | 60-70% working ERP demonstration"
p.font.size = Pt(14)
p.font.color.rgb = RGBColor(211, 229, 244)

# 2. Problem and objective
slide = prs.slides.add_slide(blank)
add_background(slide)
add_title(slide, "Why This ERP Exists", "Replacing disconnected spreadsheets with one shared system")
add_bullets(slide, [
    "Centralize products, materials, suppliers, customers, orders, and stock.",
    "Make purchase, production, and sales update the same inventory data.",
    "Reduce duplicate entry, calculation errors, and stock surprises.",
    "Give managers live dashboard information and operational history."
], 0.8, 1.5, 5.5, 4.8, 20)
flow = slide.shapes.add_textbox(Inches(6.7), Inches(1.8), Inches(5.5), Inches(3.5))
frame = flow.text_frame
frame.clear()
for i, line in enumerate(["Supplier", "↓", "Purchase Order", "↓", "Inventory", "↓", "Production", "↓", "Finished Goods", "↓", "Sales"]):
    p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
    p.text = line
    p.alignment = PP_ALIGN.CENTER
    p.font.size = Pt(22 if line != "↓" else 18)
    p.font.bold = line != "↓"
    p.font.color.rgb = BLUE if line != "↓" else MUTED
    p.space_after = Pt(4)
add_footer(slide, 2)

# 3. Architecture and database
slide = prs.slides.add_slide(blank)
add_background(slide)
add_title(slide, "System Architecture", "Frontend, Flask business logic, and MySQL database")
for i, (label, detail, color) in enumerate([
    ("Browser UI", "HTML + CSS + Bootstrap + JavaScript", BLUE),
    ("Flask Backend", "Authentication, validation, workflows, reports", GREEN),
    ("MySQL", "Related ERP tables and transaction history", NAVY),
]):
    y = 1.35 + i * 1.65
    shape = slide.shapes.add_shape(5, Inches(1.2), Inches(y), Inches(10.8), Inches(0.95))
    shape.fill.solid(); shape.fill.fore_color.rgb = color; shape.line.fill.background()
    text = shape.text_frame.paragraphs[0]; text.text = label; text.alignment = PP_ALIGN.CENTER
    text.font.size = Pt(22); text.font.bold = True; text.font.color.rgb = WHITE
    detail_box = slide.shapes.add_textbox(Inches(1.35), Inches(y + 0.98), Inches(10.5), Inches(0.35))
    p = detail_box.text_frame.paragraphs[0]; p.text = detail; p.alignment = PP_ALIGN.CENTER; p.font.size = Pt(12); p.font.color.rgb = MUTED
add_bullets(slide, ["Users", "Products and materials", "Inventory and stock movements", "Purchases, BOM, production, sales", "Audit logs and notifications"], 0.9, 6.0, 5.2, 0.9, 12)
add_footer(slide, 3)

# 4. UI overview
slide = prs.slides.add_slide(blank)
add_background(slide)
add_title(slide, "Application Entry Points", "Landing page and role-aware login")
add_image(slide, "01-landing.png", 0.55, 1.25, 6.0, 5.6)
add_image(slide, "02-login.png", 6.8, 1.25, 5.95, 5.6)
add_footer(slide, 4)

# 5. Dashboard
slide = prs.slides.add_slide(blank)
add_background(slide)
add_title(slide, "Dashboard", "Live KPIs and three operational charts")
add_image(slide, "dashboard.png", 0.55, 1.15, 12.2, 5.8)
add_footer(slide, 5)

# 6. Master data
slide = prs.slides.add_slide(blank)
add_background(slide)
add_title(slide, "Master Data Modules", "Products, materials, suppliers, and customers are stored in MySQL")
add_image(slide, "products.png", 0.55, 1.35, 6.0, 5.3)
add_image(slide, "inventory.png", 6.8, 1.35, 5.95, 5.3)
add_label(slide, "Product CRUD", 0.65, 6.73, 5.5)
add_label(slide, "Inventory with automatic stock status", 6.9, 6.73, 5.5)
add_footer(slide, 6)

# 7. Purchase and production
slide = prs.slides.add_slide(blank)
add_background(slide)
add_title(slide, "Purchase, BOM, and Production", "The core manufacturing integration")
add_image(slide, "purchase.png", 0.55, 1.25, 4.05, 5.45)
add_image(slide, "bom.png", 4.65, 1.25, 4.05, 5.45)
add_image(slide, "production.png", 8.75, 1.25, 4.05, 5.45)
add_footer(slide, 7)

# 8. Sales/customer
slide = prs.slides.add_slide(blank)
add_background(slide)
add_title(slide, "Customers and Sales", "Customer order, stock validation, processing, and invoice")
add_image(slide, "customers.png", 0.55, 1.25, 4.05, 5.45)
add_image(slide, "sales.png", 4.65, 1.25, 4.05, 5.45)
add_bullets(slide, ["Select a customer", "Check finished-product stock", "Process sale", "Reduce inventory", "Download invoice"], 9.0, 1.6, 3.3, 3.8, 18)
add_footer(slide, 8)

# 9. Reports
slide = prs.slides.add_slide(blank)
add_background(slide)
add_title(slide, "Reports and Compulsory Features", "Documents and operational evidence for the judges")
add_image(slide, "reports.png", 0.55, 1.25, 6.5, 5.45)
add_bullets(slide, ["PDF sales invoice", "Excel inventory export", "Product QR code", "Responsive interface", "Search and validation"], 7.5, 1.6, 4.7, 3.8, 20)
add_footer(slide, 9)

# 10. Audit and notifications
slide = prs.slides.add_slide(blank)
add_background(slide)
add_title(slide, "Audit, Notifications, and Accountability", "Every important workflow can be explained after the action")
add_image(slide, "audit.png", 0.55, 1.25, 6.0, 5.45)
add_image(slide, "notifications.png", 6.8, 1.25, 5.95, 5.45)
add_footer(slide, 10)

# 11. Demo flow
slide = prs.slides.add_slide(blank)
add_background(slide)
add_title(slide, "Final Demonstration Flow", "The sequence to present to the judges")
add_bullets(slide, [
    "Login as Manager.",
    "Show dashboard and current inventory.",
    "Create and receive a purchase order; show stock increase.",
    "Open the Gear Assembly BOM.",
    "Create and complete production; show raw-material deduction and finished-stock increase.",
    "Select a customer and process a sale; show finished-stock reduction.",
    "Download PDF invoice, Excel export, and product QR code.",
    "Finish with charts, notifications, and audit log."
], 0.8, 1.35, 11.7, 4.9, 20)
add_footer(slide, 11)

# 12. Status
slide = prs.slides.add_slide(blank)
add_background(slide, NAVY)
box = slide.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(11.8), Inches(0.7))
p = box.text_frame.paragraphs[0]; p.text = "Project Status"; p.font.size = Pt(32); p.font.bold = True; p.font.color.rgb = WHITE
add_bullets(slide, [
    "Core ERP workflows are connected to MySQL.",
    "Role-based access and audit history are implemented.",
    "Reports, exports, QR code, charts, and notifications are available.",
    "Smoke tests pass and the application is ready for the competition demonstration.",
    "Before final use: rotate the exposed local database password."
], 1.0, 1.8, 11.0, 4.5, 22, RGBColor(211, 229, 244))

prs.save(OUTPUT)
print(OUTPUT)
