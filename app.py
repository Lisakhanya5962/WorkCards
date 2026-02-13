from flask import Flask, render_template, request
from PIL import Image, ImageDraw, ImageFont
import os
from io import BytesIO
import smtplib
from email.message import EmailMessage

# ================= CONFIG =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
ASSETS_DIR = os.path.join(STATIC_DIR, "assets")
OUTPUT_DIR = os.path.join(STATIC_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BACKGROUND_IMAGE = os.path.join(ASSETS_DIR, "background.jpeg")
LOGO_IMAGE = os.path.join(ASSETS_DIR, "download.jpeg")

CARD_WIDTH = 1000
CARD_HEIGHT = 600
HEADER_HEIGHT = 120
GRAY = (80, 80, 80)
PHOTO_BORDER = 6

# Gmail App Password
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

app = Flask(__name__, template_folder='.')

# ================== EMAIL FUNCTION ==================
def send_email(receiver, filename, image_bytes):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Email skipped: credentials not set")
        return
    try:
        msg = EmailMessage()
        msg["Subject"] = "Your Staff ID Card"
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver
        msg.set_content("Hello,\n\nAttached is your Staff ID Card.\n\nFrontier Regional Hospital")
        msg.add_attachment(image_bytes, maintype="image", subtype="png", filename=filename)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)

        print("Email sent successfully")
    except Exception as e:
        print("Email sending failed:", e)

# ================== ROUTES ==================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"].upper()
        position = request.form["position"].upper()
        department = request.form["department"].upper()
        email = request.form["email"]
        hospital = "FRONTIER REGIONAL HOSPITAL"
        photo = request.files["photo"]

        temp_photo = os.path.join(OUTPUT_DIR, "temp.png")
        photo.save(temp_photo)

        photo_size = request.form.get("photo_size")
        if photo_size == "1": PHOTO_WIDTH, PHOTO_HEIGHT = 200, 250
        elif photo_size == "2": PHOTO_WIDTH, PHOTO_HEIGHT = 250, 300
        elif photo_size == "3": PHOTO_WIDTH, PHOTO_HEIGHT = 300, 360
        elif photo_size == "4":
            try:
                PHOTO_WIDTH = int(request.form.get("custom_width", 250))
                PHOTO_HEIGHT = int(request.form.get("custom_height", 300))
            except ValueError:
                PHOTO_WIDTH, PHOTO_HEIGHT = 250, 300
        else:
            PHOTO_WIDTH, PHOTO_HEIGHT = 250, 300

        background = Image.open(BACKGROUND_IMAGE).resize((CARD_WIDTH, CARD_HEIGHT))
        logo = Image.open(LOGO_IMAGE).resize((150, 80))
        photo_img = Image.open(temp_photo).resize((PHOTO_WIDTH, PHOTO_HEIGHT))

        card = background.copy()
        draw = ImageDraw.Draw(card)
        draw.rectangle([(0, 0), (CARD_WIDTH, HEADER_HEIGHT)], fill=GRAY)
        logo_y = (HEADER_HEIGHT - logo.height) // 2
        card.paste(logo, (30, logo_y), logo.convert("RGBA"))

        try:
            font_name = ImageFont.truetype("arialbd.ttf", 50)
            font_position = ImageFont.truetype("arial.ttf", 32)
            font_department = ImageFont.truetype("arial.ttf", 28)
            font_hospital = ImageFont.truetype("arialbd.ttf", 36)
        except:
            font_name = font_position = font_department = font_hospital = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), hospital, font=font_hospital)
        draw.text(((CARD_WIDTH-(bbox[2]-bbox[0])//2), (HEADER_HEIGHT-(bbox[3]-bbox[1])//2)),
                  hospital, fill="white", font=font_hospital)

        photo_x, photo_y = 50, HEADER_HEIGHT + 30
        draw.rectangle([(photo_x-PHOTO_BORDER, photo_y-PHOTO_BORDER),
                        (photo_x+photo_img.width+PHOTO_BORDER, photo_y+photo_img.height+PHOTO_BORDER)],
                        fill=GRAY)
        card.paste(photo_img, (photo_x, photo_y))

        text_x, text_y = 350, HEADER_HEIGHT + 80
        draw.text((text_x, text_y), name, fill="white", font=font_name)
        draw.text((text_x, text_y+70), position, fill="white", font=font_position)
        draw.text((text_x, text_y+120), department, fill="white", font=font_department)

        filename = name.replace(" ", "_") + ".png"
        output_path = os.path.join(OUTPUT_DIR, filename)
        card.save(output_path)

        img_bytes = BytesIO()
        card.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        send_email(email, filename, img_bytes.read())

        return render_template("success.html", name=name, filename=filename)

    return render_template("index.html")

# ======= RUN SERVER =======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
