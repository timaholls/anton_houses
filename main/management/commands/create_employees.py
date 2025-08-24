from django.core.management.base import BaseCommand
from main.models import Employee, BranchOffice
import random


class Command(BaseCommand):
    help = 'Создает тестовых сотрудников (агентов)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Количество сотрудников для создания'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Получаем или создаем филиалы
        branches = self.get_or_create_branches()
        
        # Данные сотрудников
        employees_data = [
            {
                'full_name': 'Иванов Иван Иванович',
                'position': 'Руководитель офиса',
                'experience_years': 8,
                'description': '<p>Опытный специалист с многолетним стажем работы в сфере недвижимости. Специализируется на работе с премиальными объектами и VIP-клиентами.</p>',
                'achievements': '<ul><li>Более 500 успешных сделок</li><li>Лучший агент года 2023</li><li>Сертификат "Эксперт по премиальной недвижимости"</li></ul>',
                'specializations': 'Премиальная недвижимость, элитные новостройки, загородная недвижимость',
                'phone': '+7 (347) 123-45-67',
                'email': 'ivanov@century21.ru',
                'is_featured': True
            },
            {
                'full_name': 'Петрова Анна Сергеевна',
                'position': 'Агент по недвижимости',
                'experience_years': 5,
                'description': '<p>Профессиональный агент с глубоким знанием рынка недвижимости Уфы. Помогает клиентам найти идеальное жилье.</p>',
                'achievements': '<ul><li>Более 200 успешных сделок</li><li>Специалист по ипотечному кредитованию</li><li>Награда "Лучший дебют года"</li></ul>',
                'specializations': 'Ипотечное кредитование, новостройки, вторичная недвижимость',
                'phone': '+7 (347) 234-56-78',
                'email': 'petrova@century21.ru',
                'is_featured': True
            },
            {
                'full_name': 'Сидоров Дмитрий Алексеевич',
                'position': 'Агент по недвижимости',
                'experience_years': 6,
                'description': '<p>Эксперт по коммерческой недвижимости и инвестиционным проектам. Помогает инвесторам найти выгодные объекты.</p>',
                'achievements': '<ul><li>Более 150 коммерческих сделок</li><li>Сертификат по инвестиционной недвижимости</li><li>Эксперт по оценке недвижимости</li></ul>',
                'specializations': 'Коммерческая недвижимость, инвестиционные проекты, оценка недвижимости',
                'phone': '+7 (347) 345-67-89',
                'email': 'sidorov@century21.ru',
                'is_featured': False
            },
            {
                'full_name': 'Козлова Елена Викторовна',
                'position': 'Специалист по ипотеке',
                'experience_years': 7,
                'description': '<p>Специалист по ипотечному кредитованию с опытом работы в банковской сфере. Помогает клиентам выбрать оптимальную ипотечную программу.</p>',
                'achievements': '<ul><li>Более 300 одобренных ипотечных заявок</li><li>Сертификат "Ипотечный консультант"</li><li>Партнерские отношения с ведущими банками</li></ul>',
                'specializations': 'Ипотечное кредитование, банковские продукты, консультации по кредитам',
                'phone': '+7 (347) 456-78-90',
                'email': 'kozlova@century21.ru',
                'is_featured': True
            },
            {
                'full_name': 'Морозов Александр Петрович',
                'position': 'Агент по недвижимости',
                'experience_years': 4,
                'description': '<p>Молодой и энергичный специалист, специализирующийся на работе с молодыми семьями и первыми покупателями.</p>',
                'achievements': '<ul><li>Более 100 сделок с молодыми семьями</li><li>Специалист по государственным программам</li><li>Эксперт по новостройкам</li></ul>',
                'specializations': 'Новостройки, государственные программы, работа с молодыми семьями',
                'phone': '+7 (347) 567-89-01',
                'email': 'morozov@century21.ru',
                'is_featured': False
            },
            {
                'full_name': 'Новикова Ольга Дмитриевна',
                'position': 'Агент по недвижимости',
                'experience_years': 9,
                'description': '<p>Опытный агент с глубоким знанием всех районов Уфы. Специализируется на вторичной недвижимости и сделках с недвижимостью.</p>',
                'achievements': '<ul><li>Более 400 сделок с вторичной недвижимостью</li><li>Эксперт по юридическим аспектам сделок</li><li>Сертификат "Профессиональный оценщик"</li></ul>',
                'specializations': 'Вторичная недвижимость, юридическое сопровождение, оценка недвижимости',
                'phone': '+7 (347) 678-90-12',
                'email': 'novikova@century21.ru',
                'is_featured': True
            },
            {
                'full_name': 'Волков Сергей Николаевич',
                'position': 'Агент по недвижимости',
                'experience_years': 3,
                'description': '<p>Специалист по загородной недвижимости и коттеджным поселкам. Помогает клиентам найти идеальный дом за городом.</p>',
                'achievements': '<ul><li>Более 50 сделок с загородной недвижимостью</li><li>Специалист по коттеджным поселкам</li><li>Эксперт по земельным участкам</li></ul>',
                'specializations': 'Загородная недвижимость, коттеджные поселки, земельные участки',
                'phone': '+7 (347) 789-01-23',
                'email': 'volkov@century21.ru',
                'is_featured': False
            },
            {
                'full_name': 'Соколова Мария Андреевна',
                'position': 'Агент по недвижимости',
                'experience_years': 6,
                'description': '<p>Специалист по работе с корпоративными клиентами и аренде коммерческой недвижимости.</p>',
                'achievements': '<ul><li>Более 80 корпоративных сделок</li><li>Специалист по аренде коммерческой недвижимости</li><li>Сертификат "Корпоративный агент"</li></ul>',
                'specializations': 'Корпоративные клиенты, аренда коммерческой недвижимости, офисные помещения',
                'phone': '+7 (347) 890-12-34',
                'email': 'sokolova@century21.ru',
                'is_featured': False
            },
            {
                'full_name': 'Лебедев Андрей Владимирович',
                'position': 'Агент по недвижимости',
                'experience_years': 5,
                'description': '<p>Специалист по элитной недвижимости и работе с высокобюджетными клиентами.</p>',
                'achievements': '<ul><li>Более 30 сделок с элитной недвижимостью</li><li>Специалист по VIP-клиентам</li><li>Сертификат "Элитная недвижимость"</li></ul>',
                'specializations': 'Элитная недвижимость, VIP-клиенты, премиальные новостройки',
                'phone': '+7 (347) 901-23-45',
                'email': 'lebedev@century21.ru',
                'is_featured': True
            },
            {
                'full_name': 'Зайцева Ирина Сергеевна',
                'position': 'Агент по недвижимости',
                'experience_years': 4,
                'description': '<p>Специалист по работе с инвесторами и доходной недвижимости. Помогает клиентам найти выгодные инвестиционные объекты.</p>',
                'achievements': '<ul><li>Более 60 инвестиционных сделок</li><li>Специалист по доходной недвижимости</li><li>Сертификат "Инвестиционный консультант"</li></ul>',
                'specializations': 'Инвестиционная недвижимость, доходная недвижимость, работа с инвесторами',
                'phone': '+7 (347) 012-34-56',
                'email': 'zaytseva@century21.ru',
                'is_featured': False
            }
        ]
        
        created_count = 0
        for i in range(min(count, len(employees_data))):
            employee_data = employees_data[i]
            
            # Выбираем случайный филиал
            branch = random.choice(branches)
            
            # Проверяем, существует ли уже сотрудник с таким именем
            if not Employee.objects.filter(full_name=employee_data['full_name']).exists():
                employee = Employee.objects.create(
                    full_name=employee_data['full_name'],
                    position=employee_data['position'],
                    branch=branch,
                    experience_years=employee_data['experience_years'],
                    description=employee_data['description'],
                    achievements=employee_data['achievements'],
                    specializations=employee_data['specializations'],
                    phone=employee_data['phone'],
                    email=employee_data['email'],
                    is_featured=employee_data['is_featured'],
                    is_active=True
                )
                created_count += 1
                self.stdout.write(f'Создан сотрудник: {employee.full_name} - {employee.position}')
            else:
                self.stdout.write(f'Сотрудник {employee_data["full_name"]} уже существует')
        
        self.stdout.write(
            self.style.SUCCESS(f'Успешно создано {created_count} новых сотрудников')
        )

    def get_or_create_branches(self):
        """Получает или создает филиалы"""
        branches_data = [
            {
                'name': 'Офис на Ленина',
                'city': 'Уфа',
                'address': 'ул. Ленина, 15',
                'phone': '+7 (347) 123-45-67',
                'email': 'lenina@century21.ru'
            },
            {
                'name': 'Офис на Проспекте',
                'city': 'Уфа',
                'address': 'пр. Октября, 25',
                'phone': '+7 (347) 234-56-78',
                'email': 'prospekt@century21.ru'
            }
        ]
        
        branches = []
        for branch_data in branches_data:
            branch, created = BranchOffice.objects.get_or_create(
                name=branch_data['name'],
                defaults=branch_data
            )
            if created:
                self.stdout.write(f'Создан филиал: {branch.name}')
            branches.append(branch)
        
        return branches
