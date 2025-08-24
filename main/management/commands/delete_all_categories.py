from django.core.management.base import BaseCommand
from main.models import Category


class Command(BaseCommand):
    help = 'Удаляет все категории из базы данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Подтверждает удаление всех категорий',
        )

    def handle(self, *args, **options):
        categories_count = Category.objects.count()
        
        if categories_count == 0:
            self.stdout.write(
                self.style.WARNING('В базе данных нет категорий для удаления')
            )
            return
        
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    f'Найдено {categories_count} категорий для удаления. '
                    'Для подтверждения удаления используйте флаг --confirm'
                )
            )
            return
        
        # Удаляем все категории
        deleted_count = Category.objects.all().delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно удалено {deleted_count} категорий из базы данных'
            )
        )
