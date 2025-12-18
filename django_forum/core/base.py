"""
SOLID PRINCIPLES DEMONSTRATION - ABSTRACTIONS LAYER

This module defines interfaces and abstract classes that demonstrate:
- INTERFACE SEGREGATION (I): Small, focused interfaces (IVoteQuery, IVoteCommand)
- DEPENDENCY INVERSION (D): Abstractions that high-level modules depend on
- LISKOV SUBSTITUTION (L): Base classes with guaranteed behavior for all implementations

Key concepts:
1. Protocols define "what" can be done (interfaces for type checking)
2. ABCs provide "how" it's commonly done (reusable implementations)
3. Composition allows building complex behavior from simple parts

Usage:
- IVoteQuery: For read-only operations (statistics, analytics)
- IVoteCommand: For write operations (voting, deleting votes)
- IVoteRepository: Full functionality (both reading and writing)
- Base classes: Inherit to get common implementations
"""

from abc import ABC, abstractmethod
from typing import Protocol


class IVoteQuery(Protocol):
    @abstractmethod
    def get_votes_for_object(self, obj): ...

    @abstractmethod
    def get_upvotes(self, obj): ...

    @abstractmethod
    def get_downvotes(self, obj): ...

    @abstractmethod
    def get_vote_count(self, obj) -> int: ...

    @abstractmethod
    def get_vote_score(self, obj) -> int: ...

    @abstractmethod
    def get_user_vote(self, obj, user): ...


class IVoteCommand(Protocol):
    @abstractmethod
    def vote(self, obj, user, vote_type) -> str: ...

    @abstractmethod
    def delete_vote(self, obj, user) -> None: ...


class IReputationCalculator(Protocol):
    @abstractmethod
    def calculate(self, model_name, vote_type, **kwargs) -> int: ...


class IVoteRepository(IVoteQuery, IVoteCommand, Protocol):
    pass


class IReputationService(IReputationCalculator, Protocol):
    @abstractmethod
    def apply_change(self, profile, points) -> None: ...



class BaseVoteQuery(ABC):
    @abstractmethod
    def get_votes_for_object(self, obj): ...

    def get_upvotes(self, obj):
        votes = self.get_votes_for_object(obj)
        return [v for v in votes if getattr(v, 'vote_type', None) == 'up']

    def get_downvotes(self, obj):
        votes = self.get_votes_for_object(obj)
        return [v for v in votes if getattr(v, 'vote_type', None) == 'down']

    def get_vote_count(self, obj) -> int:
        upvotes = len(self.get_upvotes(obj))
        downvotes = len(self.get_downvotes(obj))
        return upvotes - downvotes

    def get_vote_score(self, obj) -> int:
        return len(self.get_upvotes(obj)) - len(self.get_downvotes(obj))

    @abstractmethod
    def get_user_vote(self, obj, user): ...


class BaseVoteCommand(ABC):
    @abstractmethod
    def vote(self, obj, user, vote_type) -> str: ...

    def delete_vote(self, obj, user) -> None:
        raise NotImplementedError("Vote deletion is not supported")


class BaseVoteRepository(BaseVoteQuery, BaseVoteCommand):
    pass
