from django.core.management.base import BaseCommand
from main.models import Article, Category


class Command(BaseCommand):
    help = 'Очищает все данные статей и категорий из базы данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Подтверждает удаление всех данных',
        )
        parser.add_argument(
            '--articles-only',
            action='store_true',
            help='Удаляет только статьи',
        )
        parser.add_argument(
            '--categories-only',
            action='store_true',
            help='Удаляет только категории',
        )

    def handle(self, *args, **options):
        articles_count = Article.objects.count()
        categories_count = Category.objects.count()
        
        if articles_count == 0 and categories_count == 0:
            self.stdout.write(
                self.style.WARNING('В базе данных нет статей и категорий для удаления')
            )
            return
        
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    f'Найдено {articles_count} статей и {categories_count} категорий для удаления. '
                    'Для подтверждения удаления используйте флаг --confirm'
                )
            )
            return
        
        deleted_articles = 0
        deleted_categories = 0
        
        # Удаляем статьи
        if not options['categories_only']:
            if articles_count > 0:
                deleted_articles = Article.objects.all().delete()[0]
                self.stdout.write(
                    self.style.SUCCESS(f'Удалено {deleted_articles} статей')
                )
        
        # Удаляем категории
        if not options['articles_only']:
            if categories_count > 0:
                deleted_categories = Category.objects.all().delete()[0]
                self.stdout.write(
                    self.style.SUCCESS(f'Удалено {deleted_categories} категорий')
                )
        
        total_deleted = deleted_articles + deleted_categories
        self.stdout.write(
            self.style.SUCCESS(
                f'Очистка завершена. Всего удалено {total_deleted} записей'
            )
        )
