"""
accounts/utils.py — Rasm siqish va qayta o'lchamlash yordamchi funksiyalari.

Qo'llab-quvvatlanadigan formatlar:
  Kirish: JPG, JPEG, PNG, WEBP, GIF, BMP, TIFF, HEIC, HEIF, AVIF
  Chiqish: WebP (eng samarali siqish) yoki JPEG (progressiv)

Jarayon:
  1. Faylni ochish (HEIC/HEIF uchun pillow-heif avtomatik ishga tushadi)
  2. EXIF orientation — telefon rasmlarini to'g'rilash
  3. RGBA/P/LA → RGB konvertatsiya
  4. Proporsional kichraytirish (max 2400×2400 px, Retina uchun)
  5. Siqish va Django ContentFile qaytarish
"""
import io
import os
import logging
from PIL import Image
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

# HEIC/HEIF formatlarini qo'llab-quvvatlash (iPhone rasmlar)
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORTED = True
    logger.info("[UTILS] HEIC/HEIF format qo'llab-quvvatlash yoqildi.")
except ImportError:
    HEIC_SUPPORTED = False
    logger.warning(
        "[UTILS] pillow-heif o'rnatilmagan. "
        "HEIC/HEIF formatlar qo'llab-quvvatlanmaydi. "
        "O'rnatish: pip install pillow-heif"
    )

# Sozlamalar
MAX_WIDTH  = 2400   # px (Retina ekranlar uchun — eski 1200 dan oshirildi)
MAX_HEIGHT = 2400   # px
QUALITY    = 88     # % (WebP / JPEG uchun — yaxshi sifat/hajm balansi)
OUTPUT_FMT = 'WEBP' # saqlash formati (WebP eng yaxshi siqadi, barcha zamonaviy brauzerlarda ishlaydi)


def compress_image(
    uploaded_file,
    max_width: int = MAX_WIDTH,
    max_height: int = MAX_HEIGHT,
    quality: int = QUALITY,
    output_format: str = OUTPUT_FMT,
) -> tuple:
    """
    Yuklangan rasmni siqib, kichraytirib qaytaradi.

    Args:
        uploaded_file: Django UploadedFile yoki fayl ob'ekti
        max_width:     Maksimal kenglik (px), default 2400
        max_height:    Maksimal balandlik (px), default 2400
        quality:       Siqish sifati 1-100, default 88
        output_format: Chiqish formati ('WEBP' yoki 'JPEG'), default 'WEBP'

    Returns:
        (ContentFile, ext) — siqilgan fayl va kengaytma ('webp' yoki 'jpeg')

    Raises:
        Exception: Rasm ochib bo'lmasa yoki noto'g'ri format bo'lsa
    """
    img = Image.open(uploaded_file)
    logger.debug(
        "[UTILS] Rasm ochildi | format=%s | size=%s | mode=%s",
        img.format, img.size, img.mode
    )

    # EXIF orientation — telefon rasmlarini to'g'rilash (270° burilgan rasmlar)
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass  # EXIF yo'q bo'lsa — muammo emas

    # RGBA / P (Palette) / LA → RGB (JPEG alpha kanalini qabul qilmaydi)
    if img.mode in ('RGBA', 'P', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        try:
            background.paste(img, mask=img.split()[3])  # Alpha kanal bilan paste
        except (IndexError, ValueError):
            background.paste(img)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Proporsional kichraytirish (agar kerak bo'lsa)
    original_size = img.size
    if img.width > max_width or img.height > max_height:
        img.thumbnail((max_width, max_height), Image.LANCZOS)
        logger.debug(
            "[UTILS] Rasm kichraytirildi | %s → %s",
            original_size, img.size
        )

    # Xotiraga yozish (diskka emas)
    buffer = io.BytesIO()

    save_kwargs = {
        'format':   output_format,
        'quality':  quality,
        'optimize': True,
    }

    # Progressiv saqlash — JPEG uchun sekin yuklanishda sifat oshadi
    if output_format.upper() in ('JPEG', 'JPG'):
        save_kwargs['progressive'] = True

    img.save(buffer, **save_kwargs)
    buffer.seek(0)

    ext = output_format.lower()  # 'webp' yoki 'jpeg'
    compressed_size = buffer.getbuffer().nbytes

    logger.debug(
        "[UTILS] Rasm siqildi | format=%s | hajm=%d KB",
        ext, compressed_size // 1024
    )

    return ContentFile(buffer.read()), ext


def compress_and_replace(
    instance_field_value,
    upload_to_path: str,
    original_name: str,
    **kwargs,
) -> tuple:
    """
    Model.save() ichida chaqirish uchun qisqa wrapper.
    Siqilgan rasm ContentFile va yangi fayl nomini qaytaradi.

    Args:
        instance_field_value: Model ImageField qiymati
        upload_to_path:       Yuklash yo'li (hujjat uchun)
        original_name:        Asl fayl nomi

    Returns:
        (ContentFile, new_filename) tuple
    """
    content, ext = compress_image(instance_field_value, **kwargs)
    base_name = os.path.splitext(original_name)[0]
    new_name  = f"{base_name}.{ext}"
    return content, new_name
