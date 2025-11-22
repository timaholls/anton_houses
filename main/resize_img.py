import os
import datetime
import random
from io import BytesIO
from PIL import Image, ExifTags, PngImagePlugin
from logging import Logger
import piexif
from pathlib import Path

try:
    import cairosvg
except Exception:
    cairosvg = None


class ImageProcessor:
    def __init__(self, logger: Logger, max_size=(1000, 1000), max_kb=100, ):
        self.max_size = max_size
        self.max_kb = max_kb
        self.logger = logger

    def print_image_metadata(self, img):
        # print("== МЕТАДАННЫЕ ИЗОБРАЖЕНИЯ ==")
        # print(f"Формат: {img.format}")
        # print(f"Размер: {img.size}")
        # print(f"Цветовой режим: {img.mode}")
        pass

    def generate_random_date(self):
        year = random.choice([2021, 2022, 2023])
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        return f"{year:04d}:{month:02d}:{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

    def resize_and_compress(self, input_bytes):
        try:
            img = Image.open(input_bytes)
        except Exception as e:
            self.logger.error(f"Проблема открытия изображения: {e}")
            return None

        # print("\nИсходные данные:")
        self.print_image_metadata(img)

        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        else:
            img = img.convert('RGB')

        img.thumbnail(self.max_size)

        quality = 95
        while quality >= 10:
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality)
            size_kb = buffer.tell() / 1024
            if size_kb <= self.max_kb:
                # print(f"\n✅ Сжатие успешно ({size_kb:.2f} КБ, качество: {quality})")
                buffer.seek(0)
                return buffer
            quality -= 5

        self.logger.warning("\n❌ Не удалось сжать до нужного размера")
        return None

    def _ensure_svg_to_png(self, svg_path: Path, scale_width_px: int) -> Image.Image:
        """Конвертирует SVG в PNG через cairosvg"""
        if cairosvg is None:
            raise RuntimeError(
                "Требуется пакет 'cairosvg'. Установите зависимости из req.txt или выполните: pip install cairosvg"
            )
        with open(svg_path, "rb") as f:
            svg_bytes = f.read()
        png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=scale_width_px)
        return Image.open(BytesIO(png_bytes)).convert("RGBA")

    def add_watermark(self, img, full_coverage: bool = True, opacity: float = 0.15, 
                     relative_width: float = 0.2, position: str = "center", margin_px: int = 24):
        """Добавляет водяной знак как в watermark_on_save.py"""
        try:
            # Проверяем доступность cairosvg
            if cairosvg is None:
                self.logger.warning("cairosvg недоступен. Пропускаем добавление водяного знака.")
                return img
            
            # Получаем путь к SVG логотипу из корня проекта
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            logo_path = project_root / "pic-logo.svg"
            
            # Также проверяем в media/logo/
            if not logo_path.exists():
                try:
                    from django.conf import settings
                    media_root = Path(settings.MEDIA_ROOT)
                    logo_path = media_root / 'logo' / 'pic-logo.svg'
                except:
                    pass
            
            if not logo_path.exists():
                self.logger.warning(f"Логотип не найден: {logo_path}. Пропускаем добавление водяного знака.")
                return img
            
            # Конвертируем изображение в RGBA
            base = img.convert("RGBA")
            
            # Определяем размер водяного знака
            if full_coverage:
                target_size = int(min(base.width, base.height) * 0.8)
                target_logo_width = max(1, target_size)
            else:
                target_logo_width = max(1, int(base.width * relative_width))
            
            # Конвертируем SVG в PNG
            logo_rgba = self._ensure_svg_to_png(logo_path, target_logo_width)
            
            # Применяем прозрачность
            if opacity < 0:
                opacity = 0
            if opacity > 1:
                opacity = 1
            if logo_rgba.mode != "RGBA":
                logo_rgba = logo_rgba.convert("RGBA")
            r, g, b, a = logo_rgba.split()
            a = a.point(lambda p: int(p * opacity))
            logo_rgba = Image.merge("RGBA", (r, g, b, a))
            
            # Определяем позицию
            if position == "center":
                x = (base.width - logo_rgba.width) // 2
                y = (base.height - logo_rgba.height) // 2
            else:  # bottom-right
                x = base.width - logo_rgba.width - margin_px
                y = base.height - logo_rgba.height - margin_px
            
            # Накладываем водяной знак используя alpha_composite
            composed = base.copy()
            composed.alpha_composite(logo_rgba, dest=(max(0, x), max(0, y)))
            
            # Конвертируем обратно в RGB
            rgb = composed.convert("RGB")
            
            return rgb
            
        except Exception as e:
            self.logger.warning(f"Ошибка добавления водяного знака: {e}")
            return img  # Возвращаем исходное изображение при ошибке

    def update_metadata(self, img_bytes):
        try:
            img = Image.open(img_bytes)
            img_bytes.seek(0)
        except Exception as e:
            self.logger.error(f"Проблема открытия изображения для обновления метаданных: {e}")
            return None

        random_date_str = self.generate_random_date()
        # print("\n== ОБНОВЛЕНИЕ МЕТАДАННЫХ ==")
        # print(f"Новая дата: {random_date_str}")

        output_bytes = BytesIO()
        if img.format.upper() == "JPEG":
            try:

                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
                exif_dict["0th"][piexif.ImageIFD.Artist] = 'century21-mir-v-kvadratah'
                exif_dict["0th"][piexif.ImageIFD.DateTime] = random_date_str
                exif_bytes = piexif.dump(exif_dict)
                img.save(output_bytes, "jpeg", exif=exif_bytes)
                # print("✅ Обновлены метаданные для JPEG")
            except Exception as e:
                self.logger.warning(f"❌ Неудачное обновление метаданных для JPEG: {e}")
        elif img.format.upper() == "PNG":
            try:
                pnginfo = PngImagePlugin.PngInfo()
                pnginfo.add_text("Author", 'century21-mir-v-kvadratah')
                pnginfo.add_text("Date", random_date_str)
                img.save(output_bytes, "png", pnginfo=pnginfo)
                # print("✅ Обновлены метаданные для PNG")
            except Exception as e:
                self.logger.warning(f"❌ Неудачное обновление метаданных для PNG: {e}")
        else:
            self.logger.warning(f"❌ Обновление метаданных не реализовано для {img.format}")

        output_bytes.seek(0)
        return output_bytes

    def process(self, input_bytes):
        processed_bytes = self.resize_and_compress(input_bytes)
        # with open('temp_image.jpg', 'wb') as temp_file:
        #     temp_file.write(processed_bytes)
        if processed_bytes:
            # Добавляем водяной знак перед обновлением метаданных
            # Используем те же параметры, что и в watermark_on_save.py
            try:
                img = Image.open(processed_bytes)
                processed_bytes.seek(0)
                img_with_watermark = self.add_watermark(
                    img,
                    full_coverage=True,
                    opacity=0.15,
                    relative_width=0.2,
                    position="center"
                )
                
                # Сохраняем изображение с водяным знаком во временный буфер
                watermark_buffer = BytesIO()
                img_with_watermark.save(watermark_buffer, format='JPEG', quality=92)
                watermark_buffer.seek(0)
                processed_bytes = watermark_buffer
            except Exception as e:
                self.logger.warning(f"Ошибка при добавлении водяного знака, продолжаем без него: {e}")
            
            processed_bytes = self.update_metadata(processed_bytes)
            return processed_bytes
        raise Exception("Не удалось обработать изображение")
        # return None