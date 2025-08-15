from django.core.management.base import BaseCommand
from main.models import BranchOffice, Employee


class Command(BaseCommand):
    help = 'Создает тестовые офисы продаж и сотрудников'

    def handle(self, *args, **options):
        offices_data = [
            {
                'name': 'Офис на Ленина',
                'city': 'Уфа',
                'address': 'ул. Ленина, 1',
                'phone': '+7 347 201-94-78',
                'email': 'office-lenina@antonhaus.ru',
                'schedule': 'Пн-Пт: 9:00-18:00',
                'description': '<p>Центральный офис продаж CENTURY 21 в Уфе.</p>',
                'employees': [
                    {'full_name': 'Иванов Иван Иванович', 'position': 'Руководитель офиса', 'phone': '+7 900 000-00-01', 'email': 'ivanov@antonhaus.ru'},
                    {'full_name': 'Петров Петр Петрович', 'position': 'Агент по недвижимости', 'phone': '+7 900 000-00-02', 'email': 'petrov@antonhaus.ru'},
                ]
            },
            {
                'name': 'Офис на Проспекте',
                'city': 'Уфа',
                'address': 'пр-т Октября, 10',
                'phone': '+7 347 201-94-79',
                'email': 'office-prospect@antonhaus.ru',
                'schedule': 'Пн-Сб: 10:00-19:00',
                'description': '<p>Офис обслуживания клиентов на проспекте Октября.</p>',
                'employees': [
                    {'full_name': 'Сидорова Анна Викторовна', 'position': 'Специалист по ипотеке', 'phone': '+7 900 000-00-03', 'email': 'sidorova@antonhaus.ru'},
                    {'full_name': 'Кузнецов Дмитрий Алексеевич', 'position': 'Агент по недвижимости', 'phone': '+7 900 000-00-04', 'email': 'kuznetsov@antonhaus.ru'},
                ]
            },
        ]

        created_offices = 0
        created_employees = 0

        for office_data in offices_data:
            office, created = BranchOffice.objects.get_or_create(
                name=office_data['name'],
                defaults={
                    'city': office_data['city'],
                    'address': office_data['address'],
                    'phone': office_data['phone'],
                    'email': office_data['email'],
                    'schedule': office_data['schedule'],
                    'description': office_data['description'],
                }
            )
            if created:
                created_offices += 1

            for emp in office_data['employees']:
                _, emp_created = Employee.objects.get_or_create(
                    branch=office,
                    full_name=emp['full_name'],
                    defaults={
                        'position': emp['position'],
                        'phone': emp['phone'],
                        'email': emp['email'],
                        'is_active': True,
                    }
                )
                if emp_created:
                    created_employees += 1

        self.stdout.write(self.style.SUCCESS(
            f'Создано офисов: {created_offices}, сотрудников: {created_employees}'
        )) 