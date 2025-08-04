from django.core.management.base import BaseCommand
from main.models import Article

class Command(BaseCommand):
    help = 'Добавляет связанные статьи к демонстрационной статье'

    def handle(self, *args, **options):
        # Находим демонстрационную статью
        try:
            demo_article = Article.objects.get(title='Как взять ипотеку без первоначального взноса в 2025 году')
        except Article.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Демонстрационная статья не найдена!')
            )
            return

        # Находим статьи для связи
        related_titles = [
            'История появления ипотеки в России',
            'Как купить и продать квартиру в другом городе',
            'В каком возрасте стоит покупать квартиру'
        ]

        related_articles = []
        for title in related_titles:
            try:
                article = Article.objects.get(title=title)
                related_articles.append(article)
                self.stdout.write(
                    self.style.SUCCESS(f'Найдена статья: "{article.title}"')
                )
            except Article.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Статья не найдена: "{title}"')
                )

        # Добавляем связанные статьи
        if related_articles:
            demo_article.related_articles.set(related_articles)
            self.stdout.write(
                self.style.SUCCESS(f'Добавлено {len(related_articles)} связанных статей к демонстрационной статье')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Не найдено статей для связи')
            ) 