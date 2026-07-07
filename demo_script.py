"""
ServiceHub (tadbikor.uz) — Mustaqil Ish Video Taqdimot Avtomatsiyasi
=====================================================================
Ushbu skript:
1. Chrome brauzerini avtomatik ochadi
2. Swagger UI sahifasida API endpointlarni ketma-ket namoyish qiladi
3. ReDoc sahifasini ko'rsatadi
4. Asosiy saytni (tadbikor.uz) ko'rsatadi
5. Har bir bosqichda screenshot (skrinsho't) oladi
6. Natijada barcha skrinsho'tlarni bitta PDF ga birlashtiradi

Foydalanish:
    python demo_script.py

Talablar:
    pip install selenium webdriver-manager pillow
    Google Chrome o'rnatilgan bo'lishi kerak
"""

import time
import os
import json
import sys
from datetime import datetime

# ─────────────────────────── SOZLAMALAR ───────────────────────────
BASE_URL        = "https://tadbikor.uz"
SWAGGER_URL     = f"{BASE_URL}/swagger/"
REDOC_URL       = f"{BASE_URL}/redoc/"
SCREENSHOTS_DIR = "demo_screenshots"
# ──────────────────────────────────────────────────────────────────


def setup_driver():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        driver.implicitly_wait(10)
        print("Chrome WebDriver muvaffaqiyatli ishga tushdi.")
        return driver
    except Exception as e:
        print(f"WebDriver xatosi: {e}")
        print("Yechim: pip install selenium webdriver-manager")
        sys.exit(1)


def screenshot(driver, step_name):
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S")
    filename  = f"{SCREENSHOTS_DIR}/{timestamp}_{step_name}.png"
    driver.save_screenshot(filename)
    print(f"  Skrinsho't saqlandi: {filename}")
    return filename


def slow_scroll(driver, pause=0.3):
    total_height = driver.execute_script("return document.body.scrollHeight")
    for pos in range(0, total_height, 300):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(pause)
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)


def scroll_to(driver, element, pause=0.8):
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
        element
    )
    time.sleep(pause)


def highlight(driver, element):
    driver.execute_script(
        "arguments[0].style.border='3px solid #FFD700';"
        "arguments[0].style.boxShadow='0 0 12px #FFD700';",
        element
    )
    time.sleep(0.5)


def demo_swagger(driver):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    print("\n" + "="*60)
    print("1-BOSQICH: SWAGGER UI NAMOYISHI")
    print("="*60)

    # 1.1 Swagger sahifasini ochish
    print("  -> Swagger sahifasi ochilmoqda...")
    driver.get(SWAGGER_URL)
    time.sleep(4)
    screenshot(driver, "01_swagger_bosh_sahifa")
    print("  TUSHUNTIRISH: Bu Swagger UI — DRF bilan avtomatik yaratilgan")
    print("  interaktiv API hujjati. Har bir endpoint sinab ko'rish mumkin.")
    time.sleep(3)

    # 1.2 Umumiy ko'rinish
    print("  -> Barcha endpointlarni ko'rish uchun pastga aylantirish...")
    slow_scroll(driver, pause=0.25)
    screenshot(driver, "02_swagger_barcha_endpointlar")
    print("  TUSHUNTIRISH: Jami 31 ta API endpoint + 3 ta tizim URL mavjud.")
    print("  Ular 3 ta guruhga bo'lingan: accounts, services, orders.")
    time.sleep(3)

    # 1.3 accounts bo'limi
    print("  -> accounts bo'limini ochish...")
    try:
        tags = driver.find_elements(By.CSS_SELECTOR, ".opblock-tag")
        for tag in tags:
            if "accounts" in tag.text.lower():
                scroll_to(driver, tag)
                tag.click()
                time.sleep(2)
                screenshot(driver, "03_swagger_accounts_bolimi")
                print("  TUSHUNTIRISH: accounts bo'limida Register, Login,")
                print("  Logout, Profil, OTP va Device Session endpointlari bor.")
                time.sleep(3)
                break
    except Exception as e:
        print(f"  accounts bo'limida muammo: {e}")

    # 1.4 Login endpointini sinash
    print("  -> Login (POST /api/accounts/login/) endpointini sinash...")
    try:
        driver.get(SWAGGER_URL)
        time.sleep(3)

        # Login blokni topish
        login_ops = driver.find_elements(By.CSS_SELECTOR, ".opblock-summary-path")
        for op in login_ops:
            if "login" in op.text.lower() and "refresh" not in op.text.lower():
                scroll_to(driver, op)
                op.click()
                time.sleep(1.5)
                break

        # Try it out
        try_btns = driver.find_elements(By.CSS_SELECTOR, "button.try-out__btn")
        for btn in try_btns:
            if btn.is_displayed() and "cancel" not in btn.text.lower():
                scroll_to(driver, btn)
                highlight(driver, btn)
                btn.click()
                time.sleep(1)
                break

        screenshot(driver, "04_swagger_login_try_it_out")
        print("  TUSHUNTIRISH: 'Try it out' bosish orqali real so'rov yuborilamiz.")
        time.sleep(2)

        # JSON to'ldirish
        textareas = driver.find_elements(By.CSS_SELECTOR, "textarea.body-param__text")
        if textareas:
            ta = textareas[0]
            scroll_to(driver, ta)
            ta.clear()
            ta.send_keys(json.dumps({"email": "admin@tadbikor.uz", "password": "admin123"}, indent=2))
            time.sleep(0.5)
            screenshot(driver, "05_swagger_login_json_malumot")
            print("  TUSHUNTIRISH: Login uchun email va password yuboriladi.")
            time.sleep(2)

        # Execute
        exec_btns = driver.find_elements(By.CSS_SELECTOR, "button.execute")
        if exec_btns:
            e_btn = [b for b in exec_btns if b.is_displayed()]
            if e_btn:
                scroll_to(driver, e_btn[0])
                highlight(driver, e_btn[0])
                e_btn[0].click()
                time.sleep(3)
                screenshot(driver, "06_swagger_login_javob")
                print("  TUSHUNTIRISH: Server javobi — access_token va refresh_token.")
                print("  access_token keyingi API so'rovlarda 'Authorization: Bearer TOKEN'")
                print("  ko'rinishida headerga qo'yiladi.")
                time.sleep(3)

    except Exception as e:
        print(f"  Login testida muammo: {e}")

    # 1.5 Categories — ochiq endpoint (Auth shart emas)
    print("\n  -> /api/services/categories/ endpointini sinash (Auth shart emas)...")
    try:
        driver.get(SWAGGER_URL)
        time.sleep(3)

        ops = driver.find_elements(By.CSS_SELECTOR, ".opblock-summary-path")
        for op in ops:
            if "categories" in op.text.lower():
                scroll_to(driver, op)
                op.click()
                time.sleep(1.5)
                break

        try_btns = driver.find_elements(By.CSS_SELECTOR, "button.try-out__btn")
        for btn in try_btns:
            if btn.is_displayed():
                btn.click()
                time.sleep(0.5)
                break

        exec_btns = driver.find_elements(By.CSS_SELECTOR, "button.execute")
        for btn in exec_btns:
            if btn.is_displayed():
                scroll_to(driver, btn)
                highlight(driver, btn)
                btn.click()
                time.sleep(3)
                break

        screenshot(driver, "07_swagger_categories_javob")
        print("  TUSHUNTIRISH: Bu ochiq endpoint — autentifikatsiya shart emas.")
        print("  Barcha xizmat kategoriyalari JSON formatida qaytarildi.")
        time.sleep(3)

    except Exception as e:
        print(f"  Categories testida muammo: {e}")

    # 1.6 Orders bo'limi (JWT kerak ekanligi haqida)
    print("\n  -> orders bo'limini ochib, JWT himoyasini ko'rsatish...")
    try:
        driver.get(SWAGGER_URL)
        time.sleep(3)

        tags = driver.find_elements(By.CSS_SELECTOR, ".opblock-tag")
        for tag in tags:
            if "orders" in tag.text.lower():
                scroll_to(driver, tag)
                tag.click()
                time.sleep(2)
                screenshot(driver, "08_swagger_orders_bolimi")
                print("  TUSHUNTIRISH: Orders endpointlari qulfli belgi (lock) bilan")
                print("  ko'rsatilgan — bu JWT Bearer token majburiyligini bildiradi.")
                print("  Autentifikatsiyasiz so'rov yuborilsa, 401 Unauthorized xatosi chiqadi.")
                time.sleep(3)
                break
    except Exception as e:
        print(f"  Orders bo'limida muammo: {e}")

    print("\n  SWAGGER NAMOYISHI YAKUNLANDI!")


def demo_redoc(driver):
    print("\n" + "="*60)
    print("2-BOSQICH: REDOC API HUJJATI")
    print("="*60)

    print("  -> ReDoc sahifasi ochilmoqda...")
    driver.get(REDOC_URL)
    time.sleep(4)
    screenshot(driver, "09_redoc_bosh_sahifa")
    print("  TUSHUNTIRISH: ReDoc — API hujjatining professional va chiroyli ko'rinishi.")
    print("  Chap panel — navigatsiya, o'ng panel — batafsil tavsif va kodlar.")
    time.sleep(3)

    slow_scroll(driver, pause=0.3)
    screenshot(driver, "10_redoc_endpointlar_royxati")
    print("  TUSHUNTIRISH: Har bir endpoint uchun: HTTP metod, parametrlar,")
    print("  so'rov/javob sxemalari va real kodlar ko'rsatiladi.")
    time.sleep(3)

    print("  REDOC NAMOYISHI YAKUNLANDI!")


def demo_website(driver):
    from selenium.webdriver.common.by import By

    print("\n" + "="*60)
    print("3-BOSQICH: TADBIKOR.UZ SAYTINI NAMOYISH")
    print("="*60)

    # Bosh sahifa
    print("  -> Bosh sahifa ochilmoqda...")
    driver.get(BASE_URL)
    time.sleep(4)
    screenshot(driver, "11_sayt_bosh_sahifa")
    print("  TUSHUNTIRISH: Bu ServiceMJ.uz platformasining bosh sahifasi.")
    print("  Django Templates va DRF API orqali dinamik ma'lumotlar ko'rsatilmoqda.")
    time.sleep(3)

    slow_scroll(driver, pause=0.3)
    screenshot(driver, "12_sayt_bosh_sahifa_pastki_qism")
    time.sleep(2)

    # Providers sahifasi
    print("\n  -> Ustalar (Providers) sahifasiga o'tish...")
    try:
        driver.get(f"{BASE_URL}/providers/")
        time.sleep(3)
        screenshot(driver, "13_sayt_ustalar_sahifasi")
        print("  TUSHUNTIRISH: Ro'yxatdan o'tgan ustalar — ularning profili,")
        print("  ko'nikmalar va reytinglari /api/services/providers/ endpointidan keladi.")
        time.sleep(3)
        slow_scroll(driver, pause=0.3)
        screenshot(driver, "14_sayt_ustalar_royxati")
    except Exception as e:
        print(f"  Providers sahifasida muammo: {e}")

    # Login sahifasi
    print("\n  -> Login sahifasiga o'tish...")
    try:
        driver.get(f"{BASE_URL}/login/")
        time.sleep(2.5)
        screenshot(driver, "15_sayt_login_sahifasi")
        print("  TUSHUNTIRISH: Foydalanuvchi email va parolini kiritgach,")
        print("  backend JWT tokenni yaratib cookie orqali brauzerga saqlaydi.")
        time.sleep(3)
    except Exception as e:
        print(f"  Login sahifasida muammo: {e}")

    # Register sahifasi
    print("\n  -> Ro'yxatdan o'tish sahifasiga o'tish...")
    try:
        driver.get(f"{BASE_URL}/register/")
        time.sleep(2.5)
        screenshot(driver, "16_sayt_register_sahifasi")
        print("  TUSHUNTIRISH: Yangi foydalanuvchi ro'yxatdan o'tadi.")
        print("  Backend /api/accounts/register/ endpointiga POST so'rov yuboradi.")
        time.sleep(3)
    except Exception as e:
        print(f"  Register sahifasida muammo: {e}")

    # Admin panel
    print("\n  -> Django Admin panelini ko'rsatish...")
    try:
        driver.get(f"{BASE_URL}/admin/")
        time.sleep(3)
        screenshot(driver, "17_admin_panel")
        print("  TUSHUNTIRISH: Django Admin paneli orqali ma'lumotlar bazasini")
        print("  brauzerdan turib boshqarish mumkin. Moderatsiya va monitoring uchun ishlatiladi.")
        time.sleep(3)
    except Exception as e:
        print(f"  Admin panelda muammo: {e}")

    # Swagger ga qaytish — yakuniy ko'rinish
    print("\n  -> Yakuniy ko'rinish uchun Swagger ga qaytish...")
    driver.get(SWAGGER_URL)
    time.sleep(3)
    screenshot(driver, "18_yakuniy_swagger")
    print("  TUSHUNTIRISH: Barcha endpointlar muvaffaqiyatli namoyish qilindi.")
    print("  GitHub: github.com/DasturchiMadaminjon/ServiceMJ")
    time.sleep(3)

    print("\n  SAYT NAMOYISHI YAKUNLANDI!")


def create_pdf(screenshots_dir):
    try:
        from PIL import Image

        files = sorted([
            os.path.join(screenshots_dir, f)
            for f in os.listdir(screenshots_dir)
            if f.endswith(".png")
        ])

        if not files:
            print("  PDF uchun skrinsho'tlar topilmadi.")
            return None

        images = [Image.open(f).convert("RGB") for f in files]
        pdf_path = f"ServiceHub_Demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        images[0].save(pdf_path, save_all=True, append_images=images[1:])
        print(f"\n  PDF hisobot yaratildi: {pdf_path}")
        return pdf_path

    except Exception as e:
        print(f"  PDF yaratishda xato: {e}")
        return None


def main():
    print("\n" + "="*60)
    print("SERVICEHUB (TADBIKOR.UZ) MUSTAQIL ISH NAMOYISHI")
    print("="*60)
    print(f"Boshlanish vaqti: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Sayt: {BASE_URL}")
    print(f"Swagger: {SWAGGER_URL}")
    print(f"ReDoc:   {REDOC_URL}")
    print("="*60)

    driver = setup_driver()

    try:
        demo_swagger(driver)
        demo_redoc(driver)
        demo_website(driver)

        print("\n" + "="*60)
        print("YAKUNIY HISOBOT")
        print("="*60)

        # Skrinsho'tlar soni
        if os.path.exists(SCREENSHOTS_DIR):
            count = len([f for f in os.listdir(SCREENSHOTS_DIR) if f.endswith(".png")])
            print(f"  Jami skrinsho'tlar: {count} ta")
            print(f"  Skrinsho'tlar papkasi: {SCREENSHOTS_DIR}/")

        pdf = create_pdf(SCREENSHOTS_DIR)

        print("\n" + "="*60)
        print("NAMOYISH MUVAFFAQIYATLI YAKUNLANDI!")
        print("="*60)
        print("\nTopshiriq uchun taqdim qiladigan narsalar:")
        print(f"  1. Video taqdimot (ekran yozuvingiz)")
        print(f"  2. PDF hisobot: {pdf}")
        print(f"  3. Swagger URL: {SWAGGER_URL}")
        print(f"  4. GitHub: https://github.com/DasturchiMadaminjon/ServiceMJ")
        print(f"  5. Live sayt: {BASE_URL}")

        input("\nBrauzer yopilishi uchun Enter bosing...")

    except KeyboardInterrupt:
        print("\nNamoyish to'xtatildi (Ctrl+C).")
    except Exception as e:
        print(f"\nKutilmagan xato: {e}")
        import traceback
        traceback.print_exc()
        screenshot(driver, "XATO_holati")
    finally:
        driver.quit()
        print("Brauzer yopildi.")


if __name__ == "__main__":
    main()
