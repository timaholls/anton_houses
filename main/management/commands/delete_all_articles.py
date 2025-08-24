from django.core.management.base import BaseCommand
from main.models import Article


class Command(BaseCommand):
    help = 'Удаляет все статьи из базы данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Подтверждает удаление всех статей',
        )

    def handle(self, *args, **options):
        articles_count = Article.objects.count()
        
        if articles_count == 0:
            self.stdout.write(
                self.style.WARNING('В базе данных нет статей для удаления')
            )
            return
        
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    f'Найдено {articles_count} статей для удаления. '
                    'Для подтверждения удаления используйте флаг --confirm'
                )
            )
            return
        
        # Удаляем все статьи
        deleted_count = Article.objects.all().delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно удалено {deleted_count} статей из базы данных'
            )
        )
