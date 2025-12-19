# core/tests/test_votes.py
import logging

from core.rep_rules import REPUTATION_RULES
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse
from forum.models import Answer, Question
from reviews.models import CourseReview

from votes.models import Vote

# Get logger for this module
logger = logging.getLogger(__name__)

User = get_user_model()


class VoteModelTest(TestCase):
    """Test Vote model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123",
        )
        self.question = Question.objects.create(title="Test Question", content="Test content", author=self.user)
        self.content_type = ContentType.objects.get_for_model(Question)

    def test_vote_creation(self):
        """Test vote creation with all fields"""
        vote = Vote.objects.create(
            user=self.other_user,
            content_type=self.content_type,
            object_id=self.question.pk,
            vote_type="up",
        )

        self.assertEqual(vote.user, self.other_user)
        self.assertEqual(vote.content_type, self.content_type)
        self.assertEqual(vote.object_id, self.question.pk)
        self.assertEqual(vote.vote_type, "up")
        self.assertIsNotNone(vote.created_at)

    def test_vote_string_representation(self):
        """Test vote string representation"""
        vote = Vote.objects.create(
            user=self.other_user,
            content_type=self.content_type,
            object_id=self.question.pk,
            vote_type="up",
        )

        expected_str = f"{self.other_user.username} upvoted {self.question}"
        self.assertEqual(str(vote), expected_str)

    def test_unique_together_constraint(self):
        """Test that user can only vote once per object"""
        Vote.objects.create(
            user=self.other_user,
            content_type=self.content_type,
            object_id=self.question.pk,
            vote_type="up",
        )

        # Try to create another vote for same object by same user
        with self.assertRaises(IntegrityError):
            Vote.objects.create(
                user=self.other_user,
                content_type=self.content_type,
                object_id=self.question.pk,
                vote_type="down",
            )

    def test_vote_choices(self):
        """Test that vote types are limited to valid choices"""
        # Valid vote types should work
        for vote_type in ["up", "down"]:
            vote = Vote(
                user=self.other_user,
                content_type=self.content_type,
                object_id=self.question.pk,
                vote_type=vote_type,
            )
            try:
                vote.full_clean()  # Should not raise ValidationError
            except Exception as e:
                self.fail(f"Vote type '{vote_type}' should be valid: {e}")

    def test_different_users_can_vote_same_object(self):
        """Test that different users can vote on the same object"""
        Vote.objects.create(
            user=self.other_user,
            content_type=self.content_type,
            object_id=self.question.pk,
            vote_type="up",
        )

        # Another user should be able to vote on the same object
        third_user = User.objects.create_user(username="thirduser", email="third@example.com", password="testpass123")

        Vote.objects.create(
            user=third_user,
            content_type=self.content_type,
            object_id=self.question.pk,
            vote_type="down",
        )

        self.assertEqual(Vote.objects.filter(object_id=self.question.pk).count(), 2)


class VoteableMixinTest(TestCase):
    """Test VoteableMixin functionality"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.voter = User.objects.create_user(username="voter", email="voter@example.com", password="testpass123")
        self.question = Question.objects.create(title="Test Question", content="Test content", author=self.user)

        self.user.profile.reputation_points = 0
        self.user.profile.save()
        self.initial_reputation = self.user.profile.reputation_points

    def test_get_votes(self):
        """Test get_votes method"""
        # Initially no votes
        votes = self.question.get_votes()
        self.assertEqual(votes.count(), 0)

        # Add a vote
        Vote.objects.create(
            user=self.voter,
            content_type=ContentType.objects.get_for_model(Question),
            object_id=self.question.pk,
            vote_type="up",
        )

        votes = self.question.get_votes()
        self.assertEqual(votes.count(), 1)

    def test_get_upvotes_and_downvotes(self):
        """Test get_upvotes and get_downvotes methods"""
        # Add upvote and downvote
        Vote.objects.create(
            user=self.voter,
            content_type=ContentType.objects.get_for_model(Question),
            object_id=self.question.pk,
            vote_type="up",
        )

        another_voter = User.objects.create_user(
            username="anothervoter",
            email="another@example.com",
            password="testpass123",
        )
        Vote.objects.create(
            user=another_voter,
            content_type=ContentType.objects.get_for_model(Question),
            object_id=self.question.pk,
            vote_type="down",
        )

        self.assertEqual(len(self.question.get_upvotes()), 1)
        self.assertEqual(len(self.question.get_downvotes()), 1)

    def test_get_vote_score(self):
        """Test get_vote_score method"""
        # Initially zero
        self.assertEqual(self.question.get_vote_score(), 0)

        # Add upvote
        Vote.objects.create(
            user=self.voter,
            content_type=ContentType.objects.get_for_model(Question),
            object_id=self.question.pk,
            vote_type="up",
        )
        self.assertEqual(self.question.get_vote_score(), 1)

        # Add downvote
        another_voter = User.objects.create_user(
            username="anothervoter",
            email="another@example.com",
            password="testpass123",
        )
        Vote.objects.create(
            user=another_voter,
            content_type=ContentType.objects.get_for_model(Question),
            object_id=self.question.pk,
            vote_type="down",
        )
        self.assertEqual(self.question.get_vote_score(), 0)  # 1 up - 1 down = 0

    def test_get_user_vote(self):
        """Test get_user_vote method"""
        # Anonymous user
        self.assertIsNone(self.question.get_user_vote(None))

        # Authenticated user with no vote
        self.assertIsNone(self.question.get_user_vote(self.voter))

        # Authenticated user with vote
        Vote.objects.create(
            user=self.voter,
            content_type=ContentType.objects.get_for_model(Question),
            object_id=self.question.pk,
            vote_type="up",
        )
        self.assertEqual(self.question.get_user_vote(self.voter), "up")

    def test_vote_new_upvote(self):
        """Test adding a new upvote"""
        result = self.question.vote(self.voter, "up")

        self.assertEqual(result, "added")
        self.assertEqual(self.question.get_user_vote(self.voter), "up")
        self.assertEqual(self.question.get_vote_score(), 1)

        # Check reputation was awarded
        self.user.profile.refresh_from_db()
        expected_reputation = self.initial_reputation + REPUTATION_RULES["question_upvote"]
        self.assertEqual(self.user.profile.reputation_points, expected_reputation)

    def test_vote_new_downvote(self):
        """Test adding a new downvote"""
        result = self.question.vote(self.voter, "down")

        self.assertEqual(result, "added")
        self.assertEqual(self.question.get_user_vote(self.voter), "down")
        self.assertEqual(self.question.get_vote_score(), -1)

        # Check reputation was deducted
        self.user.profile.refresh_from_db()
        expected_reputation = self.initial_reputation + REPUTATION_RULES["question_downvote"]
        self.assertEqual(self.user.profile.reputation_points, expected_reputation)

    def test_vote_toggle_off(self):
        """Test removing vote by voting same type again"""
        # Add upvote
        self.question.vote(self.voter, "up")

        # Toggle off by voting up again
        result = self.question.vote(self.voter, "up")

        self.assertEqual(result, "removed")
        self.assertIsNone(self.question.get_user_vote(self.voter))
        self.assertEqual(self.question.get_vote_score(), 0)

        # Check reputation was reversed
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.reputation_points, self.initial_reputation)

    def test_vote_change_type(self):
        """Test changing vote type"""
        # Add upvote
        self.question.vote(self.voter, "up")
        self.user.profile.refresh_from_db()
        initial_reputation = self.user.profile.reputation_points

        # Change to downvote
        result = self.question.vote(self.voter, "down")

        self.assertEqual(result, "updated")
        self.assertEqual(self.question.get_user_vote(self.voter), "down")
        self.assertEqual(self.question.get_vote_score(), -1)

        # Check reputation was updated (upvote removed, downvote added)
        self.user.profile.refresh_from_db()
        expected_reputation = (
            initial_reputation - REPUTATION_RULES["question_upvote"] + REPUTATION_RULES["question_downvote"]
        )
        self.assertEqual(self.user.profile.reputation_points, expected_reputation)

    def test_vote_own_content(self):
        """Test that users cannot vote on their own content"""
        self.question.vote(self.user, "up")  # User voting on their own question

        self.assertIsNone(self.question.get_user_vote(self.user))
        self.assertEqual(self.question.get_vote_score(), 0)

        # Reputation should not change
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.reputation_points, self.initial_reputation)


class VoteViewTest(TestCase):
    """Test vote view functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.voter = User.objects.create_user(username="voter", email="voter@example.com", password="testpass123")
        self.question = Question.objects.create(title="Test Question", content="Test content", author=self.user)
        self.content_type = ContentType.objects.get_for_model(Question)
        self.vote_url = reverse(
            "votes:vote",
            kwargs={"content_type_id": self.content_type.pk, "object_id": self.question.pk, "vote_type": "up"},
        )

    def test_vote_login_required(self):
        """Test that login is required to vote"""
        response = self.client.post(self.vote_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_vote_invalid_vote_type(self):
        """Test voting with invalid vote type"""
        self.client.login(username="voter", password="testpass123")
        invalid_url = reverse(
            "votes:vote",
            kwargs={"content_type_id": self.content_type.pk, "object_id": self.question.pk, "vote_type": "invalid"},
        )

        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_vote_nonexistent_content_type(self):
        """Test voting on non-existent content type"""
        self.client.login(username="voter", password="testpass123")
        invalid_url = reverse(
            "votes:vote",
            kwargs={"content_type_id": 9999, "object_id": self.question.pk, "vote_type": "up"},
        )

        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 404)

    # def test_vote_nonexistent_object(self):
    #     """Test voting on non-existent object"""
    #     self.client.login(username="voter", password="testpass123")
    #     invalid_url = reverse(
    #         "votes:vote",
    #         kwargs={"content_type_id": self.content_type.pk, "object_id": 9999, "vote_type": "up"},
    #     )
    #
    #     response = self.client.post(invalid_url)
    #     self.assertEqual(response.status_code, 404)

    def test_successful_upvote(self):
        """Test successful upvote via view"""
        self.client.login(username="voter", password="testpass123")

        response = self.client.post(self.vote_url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["result"], "added")
        self.assertEqual(data["user_vote"], "up")
        self.assertEqual(data["vote_count"], 1)
        self.assertEqual(data["upvotes"], 1)
        self.assertEqual(data["downvotes"], 0)

    def test_successful_downvote(self):
        """Test successful downvote via view"""
        self.client.login(username="voter", password="testpass123")
        downvote_url = reverse(
            "votes:vote",
            kwargs={"content_type_id": self.content_type.pk, "object_id": self.question.pk, "vote_type": "down"},
        )

        response = self.client.post(downvote_url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["result"], "added")
        self.assertEqual(data["user_vote"], "down")
        self.assertEqual(data["vote_count"], -1)
        self.assertEqual(data["upvotes"], 0)
        self.assertEqual(data["downvotes"], 1)

    def test_vote_own_content_via_view(self):
        """Test that users cannot vote on their own content via view"""
        self.client.login(username="testuser", password="testpass123")  # Question author

        response = self.client.post(self.vote_url)
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Cannot vote on your own content")

    def test_vote_toggle_via_view(self):
        """Test vote toggle via view"""
        self.client.login(username="voter", password="testpass123")

        # First vote
        response = self.client.post(self.vote_url)
        data = response.json()
        self.assertEqual(data["result"], "added")

        # Toggle off
        response = self.client.post(self.vote_url)
        data = response.json()
        self.assertEqual(data["result"], "removed")
        self.assertIsNone(data["user_vote"])
        self.assertEqual(data["vote_count"], 0)

    def test_vote_change_type_via_view(self):
        """Test changing vote type via view"""
        self.client.login(username="voter", password="testpass123")

        # Upvote first
        response = self.client.post(self.vote_url)
        self.assertEqual(response.json()["user_vote"], "up")

        # Change to downvote
        downvote_url = reverse(
            "votes:vote",
            kwargs={"content_type_id": self.content_type.pk, "object_id": self.question.pk, "vote_type": "down"},
        )
        response = self.client.post(downvote_url)
        data = response.json()

        self.assertEqual(data["result"], "updated")
        self.assertEqual(data["user_vote"], "down")
        self.assertEqual(data["vote_count"], -1)


# votes/tests.py - Fix the reputation tests


class ReputationRulesTest(TestCase):
    """Test reputation rules application"""

    def setUp(self):
        self.user = User.objects.create_user(username="author", email="author@example.com", password="testpass123")
        self.voter = User.objects.create_user(username="voter", email="voter@example.com", password="testpass123")
        # Reset reputation to known value
        self.user.profile.reputation_points = 0
        self.user.profile.save()
        self.initial_reputation = self.user.profile.reputation_points

    def test_question_upvote_reputation(self):
        """Test reputation change for question upvote"""
        question = Question.objects.create(title="Test Question", content="Test content", author=self.user)

        question.vote(self.voter, "up")
        self.user.profile.refresh_from_db()

        expected_reputation = self.initial_reputation + REPUTATION_RULES["question_upvote"]
        self.assertEqual(self.user.profile.reputation_points, expected_reputation)

    def test_question_downvote_reputation(self):
        """Test reputation change for question downvote"""
        question = Question.objects.create(title="Test Question", content="Test content", author=self.user)

        question.vote(self.voter, "down")
        self.user.profile.refresh_from_db()

        expected_reputation = self.initial_reputation + REPUTATION_RULES["question_downvote"]
        self.assertEqual(self.user.profile.reputation_points, expected_reputation)

    def test_answer_upvote_reputation(self):
        """Test reputation change for answer upvote"""
        question = Question.objects.create(title="Test Question", content="Test content", author=self.user)
        answer = Answer.objects.create(question=question, content="Test answer", author=self.user)

        answer.vote(self.voter, "up")
        self.user.profile.refresh_from_db()

        expected_reputation = self.initial_reputation + REPUTATION_RULES["answer_upvote"]
        self.assertEqual(self.user.profile.reputation_points, expected_reputation)

    def test_review_upvote_reputation(self):
        """Test reputation change for review upvote"""
        review = CourseReview.objects.create(
            author=self.user,
            title="Test Review",
            content="Test review content",
            rating=5,
            course_name="Test Course",
        )

        review.vote(self.voter, "up")
        self.user.profile.refresh_from_db()

        expected_reputation = self.initial_reputation + REPUTATION_RULES["review_upvote"]
        self.assertEqual(self.user.profile.reputation_points, expected_reputation)

    def test_no_reputation_for_self_vote(self):
        """Test that self-voting doesn't affect reputation"""
        question = Question.objects.create(title="Test Question", content="Test content", author=self.user)

        # User tries to vote on their own content
        question.vote(self.user, "up")

        self.user.profile.refresh_from_db()
        # Reputation should remain unchanged
        self.assertEqual(self.user.profile.reputation_points, self.initial_reputation)


class VoteIntegrationTest(TestCase):
    """Integration tests for voting system"""

    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(username="author", email="author@example.com", password="testpass123")
        self.voter1 = User.objects.create_user(username="voter1", email="voter1@example.com", password="testpass123")
        self.voter2 = User.objects.create_user(username="voter2", email="voter2@example.com", password="testpass123")
        self.question = Question.objects.create(
            title="Integration Test Question",
            content="Integration test content",
            author=self.author,
        )
        self.content_type = ContentType.objects.get_for_model(Question)

    def test_multiple_users_voting(self):
        """Test multiple users voting on the same object"""
        # Voter1 upvotes
        self.client.login(username="voter1", password="testpass123")
        upvote_url = reverse(
            "votes:vote",
            kwargs={"content_type_id": self.content_type.pk, "object_id": self.question.pk, "vote_type": "up"},
        )
        response = self.client.post(upvote_url)
        self.assertEqual(response.json()["vote_count"], 1)

        # Voter2 downvotes
        self.client.login(username="voter2", password="testpass123")
        downvote_url = reverse(
            "votes:vote",
            kwargs={"content_type_id": self.content_type.pk, "object_id": self.question.pk, "vote_type": "down"},
        )
        response = self.client.post(downvote_url)
        self.assertEqual(response.json()["vote_count"], 0)  # 1 up - 1 down = 0

        # Check final state
        self.assertEqual(len(self.question.get_upvotes()), 1)
        self.assertEqual(len(self.question.get_downvotes()), 1)
        self.assertEqual(self.question.get_vote_score(), 0)

    def test_vote_lifecycle(self):
        """Test complete vote lifecycle: add -> change -> remove"""
        self.client.login(username="voter1", password="testpass123")
        upvote_url = reverse(
            "votes:vote",
            kwargs={"content_type_id": self.content_type.pk, "object_id": self.question.pk, "vote_type": "up"},
        )
        downvote_url = reverse(
            "votes:vote",
            kwargs={"content_type_id": self.content_type.pk, "object_id": self.question.pk, "vote_type": "down"},
        )

        # Step 1: Add upvote
        response = self.client.post(upvote_url)
        data = response.json()
        self.assertEqual(data["result"], "added")
        self.assertEqual(data["user_vote"], "up")
        self.assertEqual(data["vote_count"], 1)

        # Step 2: Change to downvote
        response = self.client.post(downvote_url)
        data = response.json()
        self.assertEqual(data["result"], "updated")
        self.assertEqual(data["user_vote"], "down")
        self.assertEqual(data["vote_count"], -1)

        # Step 3: Remove vote
        response = self.client.post(downvote_url)
        data = response.json()
        self.assertEqual(data["result"], "removed")
        self.assertIsNone(data["user_vote"])
        self.assertEqual(data["vote_count"], 0)

    def test_reputation_accumulation(self):
        """Test that reputation accumulates correctly with multiple votes"""
        # Reset reputation to known value
        self.author.profile.reputation_points = 0
        self.author.profile.save()
        initial_reputation = self.author.profile.reputation_points

        # Use existing voters instead of creating new ones
        voters = [self.voter1, self.voter2]

        # Create one more voter to test with 3 voters
        voter3 = User.objects.create_user(
            username="voter3",
            email="voter3@example.com",
            password="testpass123",  # Unique email
        )
        voters.append(voter3)

        # All voters upvote the question
        for voter in voters:
            self.question.vote(voter, "up")

        self.author.profile.refresh_from_db()
        expected_reputation = initial_reputation + (REPUTATION_RULES["question_upvote"] * 3)
        self.assertEqual(self.author.profile.reputation_points, expected_reputation)

        # One voter changes to downvote
        self.question.vote(voters[0], "down")

        self.author.profile.refresh_from_db()
        expected_reputation = (
            initial_reputation + (REPUTATION_RULES["question_upvote"] * 2) + REPUTATION_RULES["question_downvote"]
        )
        self.assertEqual(self.author.profile.reputation_points, expected_reputation)
