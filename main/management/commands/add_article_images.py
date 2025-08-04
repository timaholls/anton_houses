from django.core.management.base import BaseCommand
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import requests
import os
from main.models import Article

class Command(BaseCommand):
    help = 'Добавляет изображения к статьям'

    def handle(self, *args, **options):
        # Словарь с URL изображений для каждой статьи
        article_images = {
            'Как купить и продать квартиру в другом городе': {
                'url': 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800&h=600&fit=crop',
                'alt': 'Кредитная карта и смартфон'
            },
            'История появления ипотеки в России': {
                'url': 'https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=800&h=600&fit=crop',
                'alt': 'Букет цветов'
            },
            'В каком возрасте стоит покупать квартиру': {
                'url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&h=600&fit=crop',
                'alt': 'Молодой человек с наушниками'
            },
            'Согласие от супруга на продажу недвижимости': {
                'url': 'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800&h=600&fit=crop',
                'alt': 'Документы и ручка'
            },
            'Как выявить потребность покупателя': {
                'url': 'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=800&h=600&fit=crop',
                'alt': 'Бизнес-встреча'
            },
            'Налоговые вычеты при покупке недвижимости': {
                'url': 'https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=800&h=600&fit=crop',
                'alt': 'Калькулятор и документы'
            },
            'Выбор района для покупки квартиры': {
                'url': 'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=800&h=600&fit=crop',
                'alt': 'Карта города'
            },
            'Ремонт квартиры: с чего начать': {
                'url': 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800&h=600&fit=crop',
                'alt': 'Инструменты для ремонта'
            },
            'Инвестиции в недвижимость: плюсы и минусы': {
                'url': 'https://images.unsplash.com/photo-1554224154-26032cdc0c0f?w=800&h=600&fit=crop',
                'alt': 'График роста инвестиций'
            },
            'Проверка документов на недвижимость': {
                'url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&h=600&fit=crop',
                'alt': 'Документы и лупа'
            }
        }

        updated_count = 0
        
        for title, image_data in article_images.items():
            try:
                article = Article.objects.get(title=title)
                
                # Если у статьи уже есть изображение, пропускаем
                if article.image:
                    self.stdout.write(
                        self.style.WARNING(f'У статьи "{title}" уже есть изображение')
                    )
                    continue
                
                # Загружаем изображение
                response = requests.get(image_data['url'])
                if response.status_code == 200:
                    # Создаем временный файл
                    img_temp = NamedTemporaryFile(delete=True)
                    img_temp.write(response.content)
                    img_temp.flush()
                    
                    # Генерируем имя файла
                    filename = f"{article.slug}.jpg"
                    
                    # Сохраняем изображение
                    article.image.save(filename, File(img_temp), save=True)
                    
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Добавлено изображение к статье: {title}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Не удалось загрузить изображение для статьи: {title}')
                    )
                    
            except Article.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Статья не найдена: {title}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка при обработке статьи "{title}": {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Успешно обновлено {updated_count} статей с изображениями')
        ) 