from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
import random
from main.models import Gallery, ResidentialComplex, SecondaryProperty, Employee, Article, SpecialOffer, BranchOffice, CompanyInfo

class Command(BaseCommand):
    help = 'Заполняет все объекты тестовыми изображениями'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие изображения перед добавлением новых',
        )

    def create_test_image(self, width=800, height=600, text="Test Image"):
        """Создает тестовое изображение с текстом"""
        # Создаем изображение
        img = Image.new('RGB', (width, height), color=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)))
        
        # Добавляем текст (упрощенная версия)
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        
        # Используем стандартный шрифт
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        # Центрируем текст
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Рисуем текст
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        # Сохраняем в байты
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)
        
        return img_io

    def create_gallery_item(self, category, object_id, title, is_main=False, order=0):
        """Создает элемент галереи с тестовым изображением"""
        # Создаем тестовое изображение
        img_io = self.create_test_image(
            width=random.randint(600, 1200),
            height=random.randint(400, 800),
            text=title
        )
        
        # Создаем файл
        filename = f"test_{category}_{object_id}_{random.randint(1000, 9999)}.jpg"
        image_file = SimpleUploadedFile(
            filename,
            img_io.getvalue(),
            content_type='image/jpeg'
        )
        
        # Создаем запись в галерее
        gallery_item = Gallery.objects.create(
            title=title,
            image=image_file,
            category=category,
            object_id=object_id,
            description=f"Тестовое изображение для {title}",
            order=order,
            is_active=True,
            is_main=is_main
        )
        
        return gallery_item

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Очищаем существующие изображения...')
            Gallery.objects.all().delete()
        
        self.stdout.write('Начинаем заполнение тестовыми изображениями...')
        
        # 1. Жилые комплексы
        complexes = ResidentialComplex.objects.all()
        for complex in complexes:
            self.stdout.write(f'Добавляем изображения для ЖК: {complex.name}')

            # Главное изображение
            self.create_gallery_item(
                'residential_complex',
                complex.id,
                f"Главное фото ЖК {complex.name}",
                is_main=True,
                order=0
            )

            # Дополнительные изображения (2-4 штуки)
            for i in range(random.randint(1, 3)):
                self.create_gallery_item(
                    'residential_complex',
                    complex.id,
                    f"Фото {i+2} ЖК {complex.name}",
                    is_main=False,
                    order=i+1
                )
        
        # 2. Вторичная недвижимость
        properties = SecondaryProperty.objects.all()
        for property in properties:
            self.stdout.write(f'Добавляем изображения для объекта: {property.name}')
            
            # Главное изображение
            self.create_gallery_item(
                'secondary_property',
                property.id,
                f"Главное фото {property.name}",
                is_main=True,
                order=0
            )
            
            # Дополнительные изображения (1-2 штуки)
            for i in range(random.randint(0, 2)):
                self.create_gallery_item(
                    'secondary_property',
                    property.id,
                    f"Фото {i+2} {property.name}",
                    is_main=False,
                    order=i+1
                )
        
        # 3. Сотрудники
        employees = Employee.objects.all()
        for employee in employees:
            self.stdout.write(f'Добавляем изображения для сотрудника: {employee.full_name}')

            # Главное фото сотрудника
            self.create_gallery_item(
                'employee',
                employee.id,
                f"Фото {employee.full_name}",
                is_main=True,
                order=0
            )
        
        # 4. Статьи
        articles = Article.objects.all()
        for article in articles:
            self.stdout.write(f'Добавляем изображения для статьи: {article.title}')

            # Главное изображение статьи
            self.create_gallery_item(
                'article',
                article.id,
                f"Изображение статьи: {article.title}",
                is_main=True,
                order=0
            )
        
        # 5. Акции
        offers = SpecialOffer.objects.all()
        for offer in offers:
            self.stdout.write(f'Добавляем изображения для акции: {offer.title}')

            # Изображение акции
            self.create_gallery_item(
                'special_offer',
                offer.id,
                f"Изображение акции: {offer.title}",
                is_main=True,
                order=0
            )
        
        # 6. Офисы
        offices = BranchOffice.objects.all()
        for office in offices:
            self.stdout.write(f'Добавляем изображения для офиса: {office.name}')

            # Главное фото офиса
            self.create_gallery_item(
                'office',
                office.id,
                f"Фото офиса: {office.name}",
                is_main=True,
                order=0
            )

            # Дополнительные фото офиса
            for i in range(random.randint(1, 2)):
                self.create_gallery_item(
                    'office',
                    office.id,
                    f"Фото {i+2} офиса: {office.name}",
                    is_main=False,
                    order=i+1
                )
        
        # 7. Компания (если есть запись)
        company_info = CompanyInfo.objects.first()
        if company_info:
            self.stdout.write(f'Добавляем изображения для компании: {company_info.company_name}')

            # Главное фото компании
            self.create_gallery_item(
                'company',
                company_info.id,
                f"Фото компании: {company_info.company_name}",
                is_main=True,
                order=0
            )

            # Дополнительные фото компании (для слайдера на главной)
            for i in range(random.randint(2, 4)):
                self.create_gallery_item(
                    'company',
                    company_info.id,
                    f"Фото {i+2} компании: {company_info.company_name}",
                    is_main=False,
                    order=i+1
                )
        
        total_images = Gallery.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Готово! Создано {total_images} тестовых изображений для всех объектов.'
            )
        )
        
        # Статистика
        self.stdout.write('\nСтатистика:')
        for category, name in Gallery.CATEGORY_CHOICES:
            count = Gallery.objects.filter(category=category).count()
            self.stdout.write(f'  {name}: {count} изображений')
