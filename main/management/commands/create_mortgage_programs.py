from django.core.management.base import BaseCommand
from main.models import MortgageProgram


class Command(BaseCommand):
    help = 'Создает тестовые ипотечные программы'

    def handle(self, *args, **options):
        # Удаляем существующие программы
        MortgageProgram.objects.all().delete()
        
        # Создаем новые программы
        programs_data = [
            {
                'name': 'Базовая',
                'rate': 18,
                'is_active': True
            },
            {
                'name': 'Семейная',
                'rate': 6,
                'is_active': True
            },
            {
                'name': 'Военная',
                'rate': 2,
                'is_active': True
            },
            {
                'name': 'IT-специалистам',
                'rate': 6,
                'is_active': True
            }
        ]
        
        created_programs = []
        for program_data in programs_data:
            program = MortgageProgram.objects.create(**program_data)
            created_programs.append(program)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Создана программа: {program.name} — {program.rate}%'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно создано {len(created_programs)} ипотечных программ'
            )
        )
