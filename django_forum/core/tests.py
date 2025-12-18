# tests/test_solid_votes.py
import sys
from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch

from django.contrib.auth import get_user_model
# Django imports
from django.test import TestCase as DjangoTestCase

# Наш код
from core.mixins import VoteableMixin
from core.repositories import DjangoVoteRepository, MemoryVoteRepository
from core.calculators import BasicReputationCalculator, DebugReputationCalculator
from core.services import ReputationService, StatisticsService, VoteManager
from core.base import IVoteQuery, IVoteCommand
from forum.models import Question, Answer
from votes.models import Vote
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class TestSOLIDPrinciples(DjangoTestCase):
    """Тесты, демонстрирующие все принципы SOLID"""

    # ===== TEST LSP (Liskov Substitution) =====
    def test_lsp_repository_substitution(self):
        """LSP: Можно заменить репозиторий без изменений в миксине"""

        # Создаем тестовый объект
        class TestModel:
            pk = 1
            author = Mock()
            author.profile = Mock()

        # Используем ORM репозиторий
        obj1 = TestModel()
        obj1._vote_repository = DjangoVoteRepository()

        # Заменяем на memory репозиторий
        obj2 = TestModel()
        obj2._vote_repository = MemoryVoteRepository()

        # LSP: Оба работают с одним и тем же интерфейсом
        self.assertTrue(hasattr(obj1._vote_repository, 'get_votes_for_object'))
        self.assertTrue(hasattr(obj2._vote_repository, 'get_votes_for_object'))
        self.assertTrue(hasattr(obj1._vote_repository, 'vote'))
        self.assertTrue(hasattr(obj2._vote_repository, 'vote'))

    # ===== TEST OCP (Open/Closed) =====
    def test_ocp_calculator_extension(self):
        """OCP: Можно добавить новый калькулятор без изменений"""

        # Базовый калькулятор
        basic_calc = BasicReputationCalculator()
        points1 = basic_calc.calculate("question", "up")

        # Новый калькулятор (расширение)
        debug_calc = DebugReputationCalculator()
        points2 = debug_calc.calculate("question", "up")

        # OCP: Оба работают, не трогая друг друга
        self.assertIsInstance(points1, int)
        self.assertEqual(points2, 0)  # Debug всегда возвращает 0

    # ===== TEST DIP (Dependency Inversion) =====
    def test_dip_dependency_injection(self):
        """DIP: Зависимости инжектятся, не создаются напрямую"""

        # Создаем мок-зависимости
        mock_repository = Mock()
        mock_calculator = Mock()

        # Наследуем миксин с кастомными фабричными методами
        class TestVoteable(VoteableMixin):
            def _create_vote_repository(self):
                return mock_repository

            def _create_reputation_calculator(self):
                return mock_calculator

        # Создаем объект
        obj = TestVoteable()

        # DIP: Зависимости были инжектированы
        self.assertIs(obj._vote_repository, mock_repository)
        self.assertIs(obj._reputation_calculator, mock_calculator)

    # ===== TEST SRP (Single Responsibility) =====
    def test_srp_separation(self):
        """SRP: Каждый класс делает одну вещь"""

        # Проверяем ответственности
        repo = DjangoVoteRepository()
        calc = BasicReputationCalculator()
        service = ReputationService

        # SRP: Каждый класс имеет четкую ответственность
        self.assertTrue(hasattr(repo, 'get_votes_for_object'))  # Работа с данными
        self.assertTrue(hasattr(calc, 'calculate'))  # Расчет
        self.assertTrue(hasattr(service, 'apply_reputation_change'))  # Применение

    # ===== TEST ISP (Interface Segregation) =====
    def test_isp_interface_separation(self):
        """ISP: Клиенты зависят только от того, что используют"""

        # Создаем моки с разными интерфейсами
        query_only = Mock(spec=IVoteQuery)
        full_repo = Mock(spec=IVoteCommand)  # Должен иметь и query, и command

        # ISP: StatisticsService нужен только query
        stats = StatisticsService(query_only)
        self.assertIs(stats.vote_query, query_only)

        # ISP: VoteManager нужен полный интерфейс
        manager = VoteManager(full_repo)
        self.assertIs(manager.vote_repository, full_repo)


class TestSOLIDWithRealModels(DjangoTestCase):
    """Тесты с реальными Django моделями"""

    def setUp(self):
        """Подготовка тестовых данных"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password123'
        )
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='password123'
        )

        # Создаем вопрос
        self.question = Question.objects.create(
            title='Test Question',
            content='Test content',
            author=self.author
        )

    def test_vote_with_real_model(self):
        """Тест голосования с реальной моделью"""
        # Первое голосование
        result1 = self.question.vote(self.user1, "up")

        # Второе голосование
        result2 = self.question.vote(self.user2, "down")

        # Базовые проверки
        self.assertIsNotNone(result1, "First vote should return a result")
        self.assertIsNotNone(result2, "Second vote should return a result")

        # Проверяем через прямой запрос к базе
        actual_votes_count = Vote.objects.filter(
            content_type=ContentType.objects.get_for_model(Question),
            object_id=self.question.id
        ).count()

        # Основные проверки
        self.assertEqual(actual_votes_count, 2,
                         f"Should have 2 votes in database, but found {actual_votes_count}")

        vote_count_from_get_votes = len(self.question.get_votes())
        self.assertEqual(vote_count_from_get_votes, 2,
                         f"len(get_votes()) should return 2, but returned {vote_count_from_get_votes}")

        vote_score = self.question.get_vote_score()
        self.assertEqual(vote_score, 0,
                         f"get_vote_score() should return 0 (1 up - 1 down), but returned {vote_score}")

    def test_vote_workflow_detailed(self):
        """Подробный тест рабочего процесса голосования"""
        # Тест 1: Голосование вверх
        result = self.question.vote(self.user1, "up")

        # Проверяем создание Vote объекта
        vote_exists = Vote.objects.filter(
            user=self.user1,
            content_type=ContentType.objects.get_for_model(Question),
            object_id=self.question.id,
            vote_type="up"
        ).exists()

        self.assertTrue(vote_exists, "Vote object should be created in database")

        # Проверяем счет голосов
        self.assertEqual(len(self.question.get_votes()), 1)
        self.assertEqual(self.question.get_vote_score(), 1)

        # Тест 2: Изменение голоса
        result = self.question.vote(self.user1, "down")

        # Проверяем обновление
        vote = Vote.objects.get(
            user=self.user1,
            content_type=ContentType.objects.get_for_model(Question),
            object_id=self.question.id
        )

        self.assertEqual(vote.vote_type, "down", "Vote should be changed to 'down'")
        self.assertEqual(len(self.question.get_votes()), 1)
        self.assertEqual(self.question.get_vote_score(), -1)

        # Тест 3: Отмена голоса
        result = self.question.vote(self.user1, "down")  # Тот же голос = отмена

        vote_exists = Vote.objects.filter(
            user=self.user1,
            content_type=ContentType.objects.get_for_model(Question),
            object_id=self.question.id
        ).exists()

        self.assertFalse(vote_exists, "Vote should be deleted (cancelled)")
        self.assertEqual(len(self.question.get_votes()), 0)
        self.assertEqual(self.question.get_vote_score(), 0)

    def test_get_vote_methods(self):
        """Тест методов получения голосов"""
        # Создаем голоса
        self.question.vote(self.user1, "up")
        self.question.vote(self.user2, "down")

        # Тестируем общее количество голосов
        total_votes = len(self.question.get_votes())
        self.assertEqual(total_votes, 2)

        # Тестируем счет голосов
        score = self.question.get_vote_score()
        self.assertEqual(score, 0)

        # Тестируем апвоуты
        upvotes = self.question.get_upvotes()
        self.assertEqual(len(upvotes), 1)

        # Тестируем даунвоуты
        downvotes = self.question.get_downvotes()
        self.assertEqual(len(downvotes), 1)

        # Тестируем голос конкретного пользователя
        user1_vote = self.question.get_user_vote(self.user1)
        user2_vote = self.question.get_user_vote(self.user2)
        self.assertEqual(user1_vote, "up")
        self.assertEqual(user2_vote, "down")

        # Тестируем неголосовавшего пользователя
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='password123'
        )
        no_vote = self.question.get_user_vote(user3)
        self.assertIsNone(no_vote)

    def test_vote_on_answer(self):
        """Тест голосования на ответе"""
        # Создаем ответ
        answer = Answer.objects.create(
            question=self.question,
            content='Test answer content',
            author=self.user1
        )

        # Голосуем за ответ
        answer.vote(self.user2, "up")
        answer.vote(self.author, "up")

        # Проверяем
        total_votes = len(answer.get_votes())
        vote_score = answer.get_vote_score()
        self.assertEqual(total_votes, 2)
        self.assertEqual(vote_score, 2)  # 2 up - 0 down = 2

    def test_multiple_upvotes_score(self):
        """Тест счета голосов при нескольких апвоутах"""
        # Создаем дополнительных пользователей с уникальными email
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='password123'
        )
        user4 = User.objects.create_user(
            username='user4',
            email='user4@example.com',
            password='password123'
        )

        # Все голосуют вверх
        self.question.vote(self.user1, "up")
        self.question.vote(self.user2, "up")
        self.question.vote(user3, "up")
        self.question.vote(user4, "up")

        total_votes = len(self.question.get_votes())
        vote_score = self.question.get_vote_score()

        self.assertEqual(total_votes, 4)
        self.assertEqual(vote_score, 4)  # 4 up - 0 down = 4
