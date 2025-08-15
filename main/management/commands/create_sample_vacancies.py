from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import Vacancy
from tinymce.models import HTMLField  # noqa: F401  # ensure tinymce is loaded


class Command(BaseCommand):
    help = 'Создает тестовые вакансии для раздела Вакансии'

    def handle(self, *args, **options):
        samples = [
            {
                'title': 'Агент по недвижимости',
                'department': 'Отдел продаж',
                'city': 'Уфа',
                'employment_type': 'fulltime',
                'salary_from': 80000,
                'salary_to': 200000,
                'description': '<p>Ищем активного и коммуникабельного специалиста по продаже недвижимости.</p>',
                'responsibilities': '<ul><li>Ведение базы объектов</li><li>Проведение показов</li><li>Сопровождение сделок</li></ul>',
                'requirements': '<ul><li>Опыт продаж приветствуется</li><li>Коммуникабельность</li><li>Грамотная речь</li></ul>',
                'benefits': '<ul><li>Обучение и наставничество</li><li>Высокий % с сделок</li><li>Дружная команда</li></ul>',
            },
            {
                'title': 'Маркетолог',
                'department': 'Маркетинг',
                'city': 'Уфа',
                'employment_type': 'fulltime',
                'salary_from': 70000,
                'salary_to': 120000,
                'description': '<p>Разработка и реализация маркетинговых кампаний по продвижению объектов.</p>',
                'responsibilities': '<ul><li>Работа с таргетом</li><li>Контент-планы</li><li>Аналитика</li></ul>',
                'requirements': '<ul><li>Опыт от 1 года</li><li>Знание инструментов рекламы</li></ul>',
                'benefits': '<ul><li>Официальное трудоустройство</li><li>Гибкий график</li></ul>',
            },
            {
                'title': 'SMM-менеджер (удаленно)',
                'department': 'Маркетинг',
                'city': 'Удаленно',
                'employment_type': 'remote',
                'salary_from': None,
                'salary_to': None,
                'description': '<p>Ведение соцсетей компании, рост вовлеченности и аудитории.</p>',
                'responsibilities': '<ul><li>Контент-план</li><li>Постинг и сторис</li><li>Коллаборации</li></ul>',
                'requirements': '<ul><li>Креативность</li><li>Опыт ведения брендов</li></ul>',
                'benefits': '<ul><li>Удаленный формат</li><li>Свободный график</li></ul>',
            },
        ]

        created_count = 0
        for data in samples:
            vacancy, created = Vacancy.objects.get_or_create(
                title=data['title'],
                defaults={
                    'department': data['department'],
                    'city': data['city'],
                    'employment_type': data['employment_type'],
                    'salary_from': data['salary_from'],
                    'salary_to': data['salary_to'],
                    'description': data['description'],
                    'responsibilities': data['responsibilities'],
                    'requirements': data['requirements'],
                    'benefits': data['benefits'],
                    'published_date': timezone.now().date(),
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Создано вакансий: {created_count}')) 