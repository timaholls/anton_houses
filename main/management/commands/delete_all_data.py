from django.core.management.base import BaseCommand
from main.models import ResidentialComplex, SecondaryProperty, Employee, EmployeeReview, BranchOffice


class Command(BaseCommand):
    help = 'Удаляет все объекты недвижимости, агентов и связанные данные'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Подтверждает удаление без дополнительных запросов'
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  ВНИМАНИЕ! Эта команда удалит ВСЕ данные:\n'
                    '- Все жилые комплексы\n'
                    '- Всю вторичную недвижимость\n'
                    '- Всех сотрудников/агентов\n'
                    '- Все отзывы о сотрудниках\n'
                    '- Все филиалы/офисы\n'
                )
            )
            
            confirm = input('Вы уверены, что хотите продолжить? (да/нет): ')
            if confirm.lower() not in ['да', 'yes', 'y', 'д']:
                self.stdout.write(self.style.ERROR('Операция отменена.'))
                return

        # Подсчитываем количество объектов перед удалением
        residential_count = ResidentialComplex.objects.count()
        secondary_count = SecondaryProperty.objects.count()
        employee_count = Employee.objects.count()
        review_count = EmployeeReview.objects.count()
        branch_count = BranchOffice.objects.count()

        self.stdout.write('Начинаю удаление данных...')

        # Удаляем отзывы о сотрудниках
        if review_count > 0:
            EmployeeReview.objects.all().delete()
            self.stdout.write(f'✅ Удалено {review_count} отзывов о сотрудниках')

        # Удаляем объекты недвижимости (это также удалит связи с агентами)
        if residential_count > 0:
            ResidentialComplex.objects.all().delete()
            self.stdout.write(f'✅ Удалено {residential_count} жилых комплексов')

        if secondary_count > 0:
            SecondaryProperty.objects.all().delete()
            self.stdout.write(f'✅ Удалено {secondary_count} объектов вторичной недвижимости')

        # Удаляем сотрудников/агентов
        if employee_count > 0:
            Employee.objects.all().delete()
            self.stdout.write(f'✅ Удалено {employee_count} сотрудников/агентов')

        # Удаляем филиалы/офисы
        if branch_count > 0:
            BranchOffice.objects.all().delete()
            self.stdout.write(f'✅ Удалено {branch_count} филиалов/офисов')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Удаление завершено!\n'
                f'Удалено объектов:\n'
                f'- Жилых комплексов: {residential_count}\n'
                f'- Вторичной недвижимости: {secondary_count}\n'
                f'- Сотрудников/агентов: {employee_count}\n'
                f'- Отзывов: {review_count}\n'
                f'- Филиалов/офисов: {branch_count}\n'
                f'\nВсе данные успешно удалены из базы данных.'
            )
        )
