import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

# ================= CONFIG =================
OUTPUT_DIR = "output"
OUTPUT_FILE = "qr_sticker_test.png"

TEST_QR_URL = "https://example.com/q/123"

STICKER_SIZE = 720
OUTER_RADIUS = 60

YELLOW = "#FFD500"
QR_COLOR = "#166077"
TEXT_COLOR = "#111111"

QR_SIZE = 400
LOGO_SIZE = 80

# ================= SETUP =================
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================= BASE STICKER =================
sticker = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(sticker)

# Outer rounded yellow box
draw.rounded_rectangle(
    (0, 0, STICKER_SIZE, STICKER_SIZE),
    radius=OUTER_RADIUS,
    fill=YELLOW
)

# ================= INNER WHITE CARD =================
MARGIN = 55
BOTTOM_SPACE = 160

WHITE_LEFT   = MARGIN
WHITE_TOP    = MARGIN
WHITE_RIGHT  = STICKER_SIZE - MARGIN
WHITE_BOTTOM = STICKER_SIZE - BOTTOM_SPACE

WHITE_WIDTH  = WHITE_RIGHT - WHITE_LEFT
WHITE_HEIGHT = WHITE_BOTTOM - WHITE_TOP

draw.rounded_rectangle(
    (WHITE_LEFT, WHITE_TOP, WHITE_RIGHT, WHITE_BOTTOM),
    radius=40,
    fill="white"
)

# ================= QR GENERATION =================
qr = qrcode.QRCode(
    version=3,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=1
)
qr.add_data(TEST_QR_URL)
qr.make(fit=True)

qr_img = qr.make_image(
    fill_color=QR_COLOR,
    back_color="white"
).convert("RGBA")

qr_img = qr_img.resize((QR_SIZE, QR_SIZE))

# ================= LOGO =================
# logo = Image.open("logo.png").convert("RGBA")
# logo = logo.resize((LOGO_SIZE, LOGO_SIZE))

# qr_img.paste(
#     logo,
#     ((QR_SIZE - LOGO_SIZE) // 2, (QR_SIZE - LOGO_SIZE) // 2),
#     mask=logo
# )

# ================= CENTER QR PERFECTLY =================
qr_x = WHITE_LEFT + (WHITE_WIDTH - QR_SIZE) // 2
qr_y = WHITE_TOP + (WHITE_HEIGHT - QR_SIZE) // 2

sticker.paste(qr_img, (qr_x, qr_y), qr_img)

# ================= FONTS =================
try:
    font_bold = ImageFont.truetype("arialbd.ttf", 36)
    font = ImageFont.truetype("arial.ttf", 26)
except:
    font_bold = font = ImageFont.load_default()

# ================= TEXT =================
# Brand name
# draw.text(
#     (STICKER_SIZE // 2, WHITE_TOP + 35),
#     "letstrackme",
#     fill=TEXT_COLOR,
#     font=font_bold,
#     anchor="mm"
# )

# Website
draw.text(
    (STICKER_SIZE // 2, qr_y + QR_SIZE + 18),
    "letstrackme.com",
    fill=TEXT_COLOR,
    font=font,
    anchor="mm"
)

# Side "Scan Me"
side_text = Image.new("RGBA", (220, 40), (0, 0, 0, 0))
side_draw = ImageDraw.Draw(side_text)
side_draw.text((110, 20), "Scan Me", fill=TEXT_COLOR, font=font, anchor="mm")

sticker.paste(
    side_text.rotate(90, expand=True),
    (WHITE_LEFT + 10, qr_y + 80),
    side_text.rotate(90, expand=True)
)

sticker.paste(
    side_text.rotate(-90, expand=True),
    (WHITE_RIGHT - 55, qr_y + 80),
    side_text.rotate(-90, expand=True)
)

# CTA
draw.text(
    (STICKER_SIZE // 2, STICKER_SIZE - 70),
    "SCAN TO CONTACT OWNER",
    fill=QR_COLOR,
    font=font_bold,
    anchor="mm"
)

# ================= SAVE =================
output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
sticker.save(output_path, "PNG")

print(f"✅ QR sticker generated: {output_path}")
