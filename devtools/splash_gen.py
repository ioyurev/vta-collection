from PIL import Image, ImageDraw, ImageFont

from vta_collection.__version__ import __version__

# Создаем основное изображение в режиме RGBA для поддержки прозрачности
img = Image.new("RGBA", (800, 400), (255, 255, 255, 255))

# Загружаем иконку с сохранением альфа-канала
icon = Image.open("../assets/icon.png").convert("RGBA")
icon = icon.resize((300, 300))

# Накладываем иконку с использованием альфа-канала как маски
img.alpha_composite(icon, (50, 50))

# Создаем контекст для рисования
draw = ImageDraw.Draw(img)

# Загружаем шрифты (с обработкой ошибок)
try:
    PILFONT = ImageFont.truetype("times.ttf", 60)
    PILFONTSMALL = ImageFont.truetype("times.ttf", 40)
except OSError:
    try:
        PILFONT = ImageFont.truetype("DejaVuSerif.ttf", 60)
        PILFONTSMALL = ImageFont.truetype("DejaVuSerif.ttf", 40)
    except OSError:
        # Используем шрифт по умолчанию с ручным указанием размера
        PILFONT = ImageFont.load_default(60)
        PILFONTSMALL = ImageFont.load_default(40)

# Рисуем основной текст
draw.text(
    (400, 200),
    f"VTA\ncollection\nv{__version__}",
    font=PILFONT,
    fill=(0, 0, 0, 255),  # Черный цвет с полной непрозрачностью
    anchor="lm",
)

# Рисуем текст "Loading..." в правом нижнем углу
draw.text(
    (800, 400),
    "Loading...",
    font=PILFONTSMALL,
    fill=(0, 0, 0, 255),  # Черный цвет с полной непрозрачностью
    anchor="rd",
)

# Конвертируем в RGB перед сохранением в PNG, если нужно уменьшить размер
# Для сохранения альфа-канала используйте img.save("splash.png")
img.convert("RGB").save("splash.png")
