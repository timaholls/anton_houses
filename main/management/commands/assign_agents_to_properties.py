from django.core.management.base import BaseCommand
from main.models import ResidentialComplex, SecondaryProperty, Employee
import random


class Command(BaseCommand):
    help = 'Привязывает объекты недвижимости к агентам в случайном порядке'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очищает существующие привязки перед назначением новых'
        )

    def handle(self, *args, **options):
        # Получаем всех активных сотрудников
        employees = list(Employee.objects.filter(is_active=True))
        
        if not employees:
            self.stdout.write(
                self.style.ERROR('Нет активных сотрудников. Сначала создайте сотрудников.')
            )
            return
        
        self.stdout.write(f'Найдено {len(employees)} активных сотрудников')
        
        # Очищаем существующие привязки, если указан флаг --clear
        if options['clear']:
            ResidentialComplex.objects.update(agent=None)
            SecondaryProperty.objects.update(agent=None)
            self.stdout.write('Существующие привязки очищены')
        
        # Привязываем новостройки
        residential_complexes = ResidentialComplex.objects.all()
        assigned_residential = 0
        
        for complex in residential_complexes:
            if not complex.agent or options['clear']:
                agent = random.choice(employees)
                complex.agent = agent
                complex.save()
                assigned_residential += 1
                self.stdout.write(f'Новостройка "{complex.name}" привязана к агенту {agent.full_name}')
        
        # Привязываем вторичную недвижимость
        secondary_properties = SecondaryProperty.objects.all()
        assigned_secondary = 0
        
        for property in secondary_properties:
            if not property.agent or options['clear']:
                agent = random.choice(employees)
                property.agent = agent
                property.save()
                assigned_secondary += 1
                self.stdout.write(f'Вторичная недвижимость "{property.name}" привязана к агенту {agent.full_name}')
        
        # Статистика по агентам
        self.stdout.write('\nСтатистика по агентам:')
        for employee in employees:
            residential_count = employee.residential_complexes.count()
            secondary_count = employee.secondary_properties.count()
            total_count = residential_count + secondary_count
            
            self.stdout.write(
                f'{employee.full_name}: {residential_count} новостроек, {secondary_count} вторичных объектов '
                f'(всего: {total_count})'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Привязка завершена! Привязано {assigned_residential} новостроек и {assigned_secondary} объектов вторичной недвижимости'
            )
        )
