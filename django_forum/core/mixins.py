"""
SOLID PRINCIPLES DEMONSTRATION - ALL PRINCIPLES IN ACTION

This module demonstrates ALL 5 SOLID principles working together:

1. SINGLE RESPONSIBILITY (S):
   - VoteableMixin delegates to specialized services
   - Doesn't contain business logic, just orchestrates

2. OPEN/CLOSED (O):
   - Easy to extend via inheritance
   - New vote types/models can be added without modification

3. LISKOV SUBSTITUTION (L):
   - Works with ANY IVoteRepository implementation
   - DjangoVoteRepository, MemoryVoteRepository, CachedVoteRepository all work

4. INTERFACE SEGREGATION (I):
   - Depends on minimal interfaces (IVoteRepository, IReputationCalculator)
   - Doesn't depend on concrete implementations

5. DEPENDENCY INVERSION (D):
   - Depends on ABSTRACTIONS (IVoteRepository), not concrete classes
   - Dependencies can be injected or overridden
   - Easy to test with mocks

BENEFITS:
- Testing: Use MemoryVoteRepository for fast, isolated tests
- Performance: Switch to CachedVoteRepository without code changes
- Maintenance: Change database logic without touching business logic
"""

from typing import Optional
from django.contrib.auth import get_user_model
from core.base import IVoteRepository, IReputationCalculator
from core.repositories import DjangoVoteRepository
from core.calculators import BasicReputationCalculator
from core.services import ReputationService

User = get_user_model()


class VoteableMixin:
    vote_repository_class = DjangoVoteRepository
    reputation_calculator_class = BasicReputationCalculator

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._vote_repository = self._create_vote_repository()
        self._reputation_calculator = self._create_reputation_calculator()

    def _create_vote_repository(self) -> IVoteRepository:
        return self.vote_repository_class()

    def _create_reputation_calculator(self) -> IReputationCalculator:
        return self.reputation_calculator_class()

    def get_votes(self):
        return self._vote_repository.get_votes_for_object(self)

    def get_upvotes(self):
        return self._vote_repository.get_upvotes(self)

    def get_downvotes(self):
        return self._vote_repository.get_downvotes(self)

    def get_vote_count(self):
        return self._vote_repository.get_vote_count(self)

    def get_vote_score(self):
        return self._vote_repository.get_vote_score(self)

    def get_user_vote(self, user: Optional[User]) -> Optional[str]:
        return self._vote_repository.get_user_vote(self, user)

    def vote(self, user: User, vote_type: str) -> str:
        if user is None or not user.is_authenticated:
            return "unauthorized"

        if hasattr(self, "author") and self.author == user:
            return "self_vote"

        old_vote_type = self.get_user_vote(user)

        result = self._vote_repository.vote(self, user, vote_type)

        if hasattr(self, "author") and self.author != user:
            self._handle_reputation(result, old_vote_type, vote_type)

        return result

    def _handle_reputation(self, result: str, old_vote_type: str, new_vote_type: str):
        model_name = self.__class__.__name__.lower()

        if result == "removed":
            points = self._reputation_calculator.calculate(
                model_name, old_vote_type, removed=True
            )
        elif result == "updated":
            points = self._reputation_calculator.calculate(
                model_name, old_vote_type, new_vote_type=new_vote_type
            )
        else:
            points = self._reputation_calculator.calculate(model_name, new_vote_type)

        self._apply_reputation_change(points)

    def _apply_reputation_change(self, points: int):
        if hasattr(self, "author") and points != 0:
            ReputationService.apply_reputation_change(self.author.profile, points)
