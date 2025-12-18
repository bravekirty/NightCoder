"""
SOLID PRINCIPLES DEMONSTRATION - OPEN/CLOSED PRINCIPLE

This module demonstrates OPEN/CLOSED PRINCIPLE (O):
- Classes are OPEN for extension: New calculators can be added via inheritance
- Classes are CLOSED for modification: Existing calculators don't need changes

Architecture:
1. ReputationCalculator (ABC): Defines the calculation contract
2. BasicReputationCalculator: Default implementation
3. DebugReputationCalculator: Extended for debugging (added WITHOUT modifying base)
4. Easy to add: DoublePointsCalculator, CappedCalculator, etc.

Key insight:
We can add NEW functionality by creating NEW classes,
not by changing EXISTING ones. This prevents bugs in stable code.
"""

from abc import ABC, abstractmethod

from core.rep_rules import REPUTATION_RULES


class ReputationCalculator(ABC):
    @abstractmethod
    def calculate(self, model_name, vote_type, **kwargs):
        pass


class BasicReputationCalculator(ReputationCalculator):
    def calculate(self, model_name, vote_type, **kwargs):
        if model_name == "coursereview":
            model_name = "review"

        vote_suffix = "upvote" if vote_type == "up" else "downvote"
        reputation_key = f"{model_name}_{vote_suffix}"

        if kwargs.get("removed"):
            return -REPUTATION_RULES.get(reputation_key, 0)
        elif kwargs.get("new_vote_type"):
            old_suffix = "upvote" if vote_type == "up" else "downvote"
            new_suffix = "upvote" if kwargs["new_vote_type"] == "up" else "downvote"
            old_points = REPUTATION_RULES.get(f"{model_name}_{old_suffix}", 0)
            new_points = REPUTATION_RULES.get(f"{model_name}_{new_suffix}", 0)
            return new_points - old_points
        else:
            return REPUTATION_RULES.get(reputation_key, 0)


class DebugReputationCalculator(ReputationCalculator):
    def calculate(self, model_name, vote_type, **kwargs):
        print(f"DEBUG: Model {model_name}, vote {vote_type}, kwargs {kwargs}")
        return 0
