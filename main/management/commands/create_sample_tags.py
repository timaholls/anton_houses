from django.core.management.base import BaseCommand
from main.models import Tag, Article

class Command(BaseCommand):
    help = 'Создает примеры тегов для статей'

    def handle(self, *args, **options):
        tags_data = [
            {
                'name': 'Ипотека',
                'h1_title': 'Статьи об ипотеке',
                'meta_title': 'Ипотека - статьи и советы | Антон Хаус',
                'meta_description': 'Полезные статьи об ипотеке, советы по получению кредита, условия банков. Читайте на сайте Антон Хаус.'
            },
            {
                'name': 'Покупка недвижимости',
                'h1_title': 'Покупка недвижимости - советы и инструкции',
                'meta_title': 'Покупка недвижимости - советы экспертов | Антон Хаус',
                'meta_description': 'Как правильно купить недвижимость? Советы экспертов, пошаговые инструкции, проверка документов.'
            },
            {
                'name': 'Продажа недвижимости',
                'h1_title': 'Продажа недвижимости - руководство',
                'meta_title': 'Продажа недвижимости - как продать быстро и выгодно | Антон Хаус',
                'meta_description': 'Советы по продаже недвижимости, оценка стоимости, подготовка документов, поиск покупателей.'
            },
            {
                'name': 'Налоги',
                'h1_title': 'Налоги при сделках с недвижимостью',
                'meta_title': 'Налоги при покупке и продаже недвижимости | Антон Хаус',
                'meta_description': 'Налоговые вычеты, НДФЛ, налог на имущество. Все о налогах при сделках с недвижимостью.'
            },
            {
                'name': 'Документы',
                'h1_title': 'Документы для сделок с недвижимостью',
                'meta_title': 'Документы для покупки и продажи недвижимости | Антон Хаус',
                'meta_description': 'Какие документы нужны для сделки с недвижимостью? Проверка документов, список необходимых бумаг.'
            },
            {
                'name': 'Ремонт',
                'h1_title': 'Ремонт квартиры - советы и инструкции',
                'meta_title': 'Ремонт квартиры - с чего начать | Антон Хаус',
                'meta_description': 'Планирование ремонта, выбор материалов, поиск подрядчиков. Советы по ремонту квартиры.'
            },
            {
                'name': 'Инвестиции',
                'h1_title': 'Инвестиции в недвижимость',
                'meta_title': 'Инвестиции в недвижимость - плюсы и минусы | Антон Хаус',
                'meta_description': 'Стоит ли инвестировать в недвижимость? Анализ рынка, стратегии инвестирования, риски и доходность.'
            },
            {
                'name': 'Законы',
                'h1_title': 'Законы о недвижимости',
                'meta_title': 'Законы о недвижимости - правовые аспекты | Антон Хаус',
                'meta_description': 'Правовые аспекты сделок с недвижимостью, изменения в законодательстве, защита прав.'
            }
        ]

        created_count = 0
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                defaults={
                    'h1_title': tag_data['h1_title'],
                    'meta_title': tag_data['meta_title'],
                    'meta_description': tag_data['meta_description']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Создан тег: {tag.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Тег уже существует: {tag.name}')
                )

        # Добавляем теги к статьям
        articles = Article.objects.all()
        for article in articles:
            # Добавляем теги в зависимости от категории и содержания
            if article.category == 'mortgage':
                tag = Tag.objects.filter(name='Ипотека').first()
                if tag:
                    article.tags.add(tag)
            
            if 'покупк' in article.title.lower() or 'купить' in article.title.lower():
                tag = Tag.objects.filter(name='Покупка недвижимости').first()
                if tag:
                    article.tags.add(tag)
            
            if 'продаж' in article.title.lower() or 'продать' in article.title.lower():
                tag = Tag.objects.filter(name='Продажа недвижимости').first()
                if tag:
                    article.tags.add(tag)
            
            if 'налог' in article.title.lower() or 'вычет' in article.title.lower():
                tag = Tag.objects.filter(name='Налоги').first()
                if tag:
                    article.tags.add(tag)
            
            if 'документ' in article.title.lower() or 'проверк' in article.title.lower():
                tag = Tag.objects.filter(name='Документы').first()
                if tag:
                    article.tags.add(tag)
            
            if 'ремонт' in article.title.lower():
                tag = Tag.objects.filter(name='Ремонт').first()
                if tag:
                    article.tags.add(tag)
            
            if 'инвестиц' in article.title.lower():
                tag = Tag.objects.filter(name='Инвестиции').first()
                if tag:
                    article.tags.add(tag)
            
            if article.category == 'laws':
                tag = Tag.objects.filter(name='Законы').first()
                if tag:
                    article.tags.add(tag)

        self.stdout.write(
            self.style.SUCCESS(f'Успешно создано {created_count} тегов и добавлены к статьям')
        ) 