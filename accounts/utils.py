"""
Rasm siqish va qayta o'lchamlash yordamchi funksiyalari.
Har qanday katta rasm qabul qilinib, WebP yoki JPEG formatida
maksimal 1200×1200 px, 85% sifatda saqlanadi.
"""
import io
import os
from PIL import Image
from django.core.files.base import ContentFile

# Sozlamalar
MAX_WIDTH  = 1200   # px
MAX_HEIGHT = 1200   # px
QUALITY    = 85     # % (WebP / JPEG)
OUTPUT_FMT = 'WEBP' # saqlash formati (WebP eng yaxshi siqadi)


def compress_image(uploaded_file, max_width=MAX_WIDTH,
                   max_height=MAX_HEIGHT, quality=QUALITY,
                   output_format=OUTPUT_FMT) -> ContentFile:
    """
    Yuklangan rasmni qabul qilib:
      1. Ochadi (PNG / JPEG / WEBP / GIF / BMP hammasi qabul)
      2. RGBA → RGB konvertatsiya (JPEG uchun alpha kanal yo'q)
      3. Proporsional kichraytiradi (agar kerak bo'lsa)
      4. Belgilangan sifatda siqadi
      5. Django ContentFile qaytaradi
    """
    img = Image.open(uploaded_file)

    # EXIF orientation — telefon rasmlarini to'g'rilash
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # RGBA / P → RGB
    if img.mode in ('RGBA', 'P', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        try:
            background.paste(img, mask=img.split()[3])
        except (IndexError, ValueError):
            background.paste(img)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Proporsional kichraytirish
    if img.width > max_width or img.height > max_height:
        img.thumbnail((max_width, max_height), Image.LANCZOS)

    # Xotiraga yozish
    buffer = io.BytesIO()
    img.save(buffer, format=output_format, quality=quality, optimize=True)
    buffer.seek(0)

    ext = output_format.lower()  # 'webp'
    return ContentFile(buffer.read()), ext


def compress_and_replace(instance_field_value, upload_to_path,
                         original_name, **kwargs):
    """
    Model.save() ichida chaqirish uchun qisqa wrapper.
    Eski faylni o'chirib, yangi siqilgan faylni qaytaradi.
    """
    content, ext = compress_image(instance_field_value, **kwargs)
    base_name = os.path.splitext(original_name)[0]
    new_name   = f"{base_name}.{ext}"
    return content, new_name
