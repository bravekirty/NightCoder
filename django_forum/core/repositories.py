"""
SOLID PRINCIPLES DEMONSTRATION - LISKOV SUBSTITUTION PRINCIPLE

This module demonstrates LISKOV SUBSTITUTION PRINCIPLE (L):
Any repository implementation can be substituted for another without breaking the system.

Implementations:
1. DjangoVoteRepository: Real database operations via Django ORM
2. MemoryVoteRepository: In-memory storage for testing (NO database required)
3. CachedVoteRepository: Adds caching on top of Django ORM

LSP Guarantees:
- All repositories have the SAME public methods
- All methods return the SAME types (List, str, None, etc.)
- Behavior is PREDICTABLE regardless of implementation

This enables:
- Easy testing (swap database for memory)
- Performance optimization (add caching transparently)
- Flexible deployments (different storage for different environments)
"""

from typing import List, Optional

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from votes.models import Vote

User = get_user_model()


def get_user_id(user):
    if hasattr(user, 'pk'):
        return user.pk
    elif hasattr(user, 'id'):
        return user.id
    elif isinstance(user, int):
        return user
    else:
        raise ValueError(f"Cannot extract ID from user object: {user}")


class BaseVoteRepository:
    def get_votes_for_object(self, obj):
        raise NotImplementedError("Must be implemented in subclasses")

    def get_upvotes(self, obj):
        votes = self.get_votes_for_object(obj)
        return [v for v in votes if getattr(v, 'vote_type', None) == 'up']

    def get_downvotes(self, obj):
        votes = self.get_votes_for_object(obj)
        return [v for v in votes if getattr(v, 'vote_type', None) == 'down']

    def get_vote_count(self, obj):
        votes = self.get_votes_for_object(obj)
        return len(votes)

    def get_vote_score(self, obj):
        upvotes = len(self.get_upvotes(obj))
        downvotes = len(self.get_downvotes(obj))
        return upvotes - downvotes

    def get_user_vote(self, obj, user):
        raise NotImplementedError("Must be implemented in subclasses")

    def vote(self, obj, user, vote_type):
        raise NotImplementedError("Must be implemented in subclasses")


class DjangoVoteRepository(BaseVoteRepository):
    def get_votes_for_object(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        return Vote.objects.filter(content_type=content_type, object_id=obj.pk)

    def get_user_vote(self, obj, user):
        if user is None or not user.is_authenticated:
            return None

        content_type = ContentType.objects.get_for_model(obj)
        try:
            vote = Vote.objects.get(user=user, content_type=content_type, object_id=obj.pk)
            return vote.vote_type
        except Vote.DoesNotExist:
            return None

    def vote(self, obj, user, vote_type):
        content_type = ContentType.objects.get_for_model(obj)

        try:
            vote = Vote.objects.get(user=user, content_type=content_type, object_id=obj.pk)

            if vote.vote_type == vote_type:
                vote.delete()
                return "removed"
            else:
                vote.vote_type = vote_type
                vote.save()
                return "updated"

        except Vote.DoesNotExist:
            Vote.objects.create(user=user, content_type=content_type, object_id=obj.pk, vote_type=vote_type)
            return "added"


class MemoryVoteRepository(BaseVoteRepository):
    _shared_votes = []

    def __init__(self):
        self.votes = []

    @classmethod
    def reset(cls):
        cls._shared_votes.clear()

    def get_votes_for_object(self, obj):
        return [v for v in self.votes if v['object_id'] == obj.pk]

    def get_user_vote(self, obj, user):
        if not user or not getattr(user, 'is_authenticated', True):
            return None

        for vote in self.votes:
            if (vote['object_id'] == obj.pk and
                    vote['user_id'] == get_user_id(user)):
                return vote['vote_type']
        return None

    def vote(self, obj, user, vote_type):
        vote_idx = None
        for i, v in enumerate(self.votes):
            if (v['object_id'] == obj.pk and
                    v['user_id'] == get_user_id(user)):
                vote_idx = i
                break

        if vote_idx is not None:
            if self.votes[vote_idx]['vote_type'] == vote_type:
                self.votes.pop(vote_idx)
                return "removed"
            else:
                self.votes[vote_idx]['vote_type'] = vote_type
                return "updated"
        else:
            vote = {
                "user_id": get_user_id(user),
                "object_id": obj.pk,
                "vote_type": vote_type,
            }
            self.votes.append(vote)
            return "added"


class CachedVoteRepository(DjangoVoteRepository):
    CACHE_TTL = 60 * 5
    CACHE_PREFIX = "votes"

    def _get_cache_key(self, obj, suffix=""):
        return f"{self.CACHE_PREFIX}:{obj.__class__.__name__}:{obj.pk}:{suffix}"

    def get_votes_for_object(self, obj) -> List[Vote]:
        cache_key = self._get_cache_key(obj, "all")
        cached = cache.get(cache_key)

        if cached is not None:
            return cached

        votes = list(super().get_votes_for_object(obj))

        cache.set(cache_key, votes, self.CACHE_TTL)
        return votes

    def get_user_vote(self, obj, user: Optional[User]) -> Optional[str]:
        if user is None or not user.is_authenticated:
            return None

        cache_key = self._get_cache_key(obj, f"user:{user.pk}")
        cached = cache.get(cache_key)

        if cached is not None:
            return cached

        vote_type = super().get_user_vote(obj, user)

        cache.set(cache_key, vote_type, self.CACHE_TTL)
        return vote_type

    def vote(self, obj, user: User, vote_type: str) -> str:
        result = super().vote(obj, user, vote_type)

        self._invalidate_cache(obj, user)

        return result

    def _invalidate_cache(self, obj, user):
        keys_to_delete = [
            self._get_cache_key(obj, "all"),
            self._get_cache_key(obj, f"user:{user.pk}"),
        ]
        cache.delete_many(keys_to_delete)
