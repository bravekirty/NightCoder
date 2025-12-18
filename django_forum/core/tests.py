from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase as DjangoTestCase
from forum.models import Answer, Question
from votes.models import Vote

from core.base import IVoteCommand, IVoteQuery
from core.calculators import BasicReputationCalculator, DebugReputationCalculator
from core.mixins import VoteableMixin
from core.repositories import DjangoVoteRepository, MemoryVoteRepository
from core.services import ReputationService, StatisticsService, VoteManager

User = get_user_model()


class TestSOLIDPrinciples(DjangoTestCase):
    def test_lsp_repository_substitution(self):
        class TestModel:
            pk = 1
            author = Mock()
            author.profile = Mock()

        obj1 = TestModel()
        obj1._vote_repository = DjangoVoteRepository()

        obj2 = TestModel()
        obj2._vote_repository = MemoryVoteRepository()

        self.assertTrue(hasattr(obj1._vote_repository, "get_votes_for_object"))
        self.assertTrue(hasattr(obj2._vote_repository, "get_votes_for_object"))
        self.assertTrue(hasattr(obj1._vote_repository, "vote"))
        self.assertTrue(hasattr(obj2._vote_repository, "vote"))

    def test_ocp_calculator_extension(self):
        basic_calc = BasicReputationCalculator()
        points1 = basic_calc.calculate("question", "up")

        debug_calc = DebugReputationCalculator()
        points2 = debug_calc.calculate("question", "up")

        self.assertIsInstance(points1, int)
        self.assertEqual(points2, 0)

    def test_dip_dependency_injection(self):
        mock_repository = Mock()
        mock_calculator = Mock()

        class TestVoteable(VoteableMixin):
            def _create_vote_repository(self):
                return mock_repository

            def _create_reputation_calculator(self):
                return mock_calculator

        obj = TestVoteable()

        self.assertIs(obj._vote_repository, mock_repository)
        self.assertIs(obj._reputation_calculator, mock_calculator)

    def test_srp_separation(self):
        repo = DjangoVoteRepository()
        calc = BasicReputationCalculator()
        service = ReputationService

        self.assertTrue(hasattr(repo, "get_votes_for_object"))
        self.assertTrue(hasattr(calc, "calculate"))
        self.assertTrue(hasattr(service, "apply_reputation_change"))

    def test_isp_interface_separation(self):
        query_only = Mock(spec=IVoteQuery)
        full_repo = Mock(spec=IVoteCommand)

        stats = StatisticsService(query_only)
        self.assertIs(stats.vote_query, query_only)

        manager = VoteManager(full_repo)
        self.assertIs(manager.vote_repository, full_repo)


class TestSOLIDWithRealModels(DjangoTestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", email="user1@example.com", password="password123")
        self.user2 = User.objects.create_user(username="user2", email="user2@example.com", password="password123")
        self.author = User.objects.create_user(username="author", email="author@example.com", password="password123")

        self.question = Question.objects.create(title="Test Question", content="Test content", author=self.author)

    def test_vote_with_real_model(self):
        result1 = self.question.vote(self.user1, "up")

        result2 = self.question.vote(self.user2, "down")

        self.assertIsNotNone(result1, "First vote should return a result")
        self.assertIsNotNone(result2, "Second vote should return a result")

        actual_votes_count = Vote.objects.filter(
            content_type=ContentType.objects.get_for_model(Question), object_id=self.question.id
        ).count()

        self.assertEqual(actual_votes_count, 2, f"Should have 2 votes in database, but found {actual_votes_count}")

        vote_count_from_get_votes = len(self.question.get_votes())
        self.assertEqual(
            vote_count_from_get_votes, 2, f"len(get_votes()) should return 2, but returned {vote_count_from_get_votes}"
        )

        vote_score = self.question.get_vote_score()
        self.assertEqual(vote_score, 0, f"get_vote_score() should return 0 (1 up - 1 down), but returned {vote_score}")

    def test_vote_workflow_detailed(self):
        self.question.vote(self.user1, "up")

        vote_exists = Vote.objects.filter(
            user=self.user1,
            content_type=ContentType.objects.get_for_model(Question),
            object_id=self.question.id,
            vote_type="up",
        ).exists()

        self.assertTrue(vote_exists, "Vote object should be created in database")

        self.assertEqual(len(self.question.get_votes()), 1)
        self.assertEqual(self.question.get_vote_score(), 1)

        self.question.vote(self.user1, "down")

        vote = Vote.objects.get(
            user=self.user1, content_type=ContentType.objects.get_for_model(Question), object_id=self.question.id
        )

        self.assertEqual(vote.vote_type, "down", "Vote should be changed to 'down'")
        self.assertEqual(len(self.question.get_votes()), 1)
        self.assertEqual(self.question.get_vote_score(), -1)

        self.question.vote(self.user1, "down")

        vote_exists = Vote.objects.filter(
            user=self.user1, content_type=ContentType.objects.get_for_model(Question), object_id=self.question.id
        ).exists()

        self.assertFalse(vote_exists, "Vote should be deleted (cancelled)")
        self.assertEqual(len(self.question.get_votes()), 0)
        self.assertEqual(self.question.get_vote_score(), 0)

    def test_get_vote_methods(self):
        self.question.vote(self.user1, "up")
        self.question.vote(self.user2, "down")

        total_votes = len(self.question.get_votes())
        self.assertEqual(total_votes, 2)

        score = self.question.get_vote_score()
        self.assertEqual(score, 0)

        upvotes = self.question.get_upvotes()
        self.assertEqual(len(upvotes), 1)

        downvotes = self.question.get_downvotes()
        self.assertEqual(len(downvotes), 1)

        user1_vote = self.question.get_user_vote(self.user1)
        user2_vote = self.question.get_user_vote(self.user2)
        self.assertEqual(user1_vote, "up")
        self.assertEqual(user2_vote, "down")

        user3 = User.objects.create_user(username="user3", email="user3@example.com", password="password123")
        no_vote = self.question.get_user_vote(user3)
        self.assertIsNone(no_vote)

    def test_vote_on_answer(self):
        answer = Answer.objects.create(question=self.question, content="Test answer content", author=self.user1)

        answer.vote(self.user2, "up")
        answer.vote(self.author, "up")

        total_votes = len(answer.get_votes())
        vote_score = answer.get_vote_score()
        self.assertEqual(total_votes, 2)
        self.assertEqual(vote_score, 2)

    def test_multiple_upvotes_score(self):
        user3 = User.objects.create_user(username="user3", email="user3@example.com", password="password123")
        user4 = User.objects.create_user(username="user4", email="user4@example.com", password="password123")

        self.question.vote(self.user1, "up")
        self.question.vote(self.user2, "up")
        self.question.vote(user3, "up")
        self.question.vote(user4, "up")

        total_votes = len(self.question.get_votes())
        vote_score = self.question.get_vote_score()

        self.assertEqual(total_votes, 4)
        self.assertEqual(vote_score, 4)
