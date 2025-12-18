"""
SOLID PRINCIPLES DEMONSTRATION - SINGLE RESPONSIBILITY PRINCIPLE

This module demonstrates SINGLE RESPONSIBILITY PRINCIPLE (S):
Each class has ONE and ONLY ONE reason to change.

Services:
1. ReputationService: ONLY applies reputation changes to profiles
2. StatisticsService: ONLY calculates statistics (depends ONLY on IVoteQuery)
3. VoteManager: ONLY manages voting operations (depends on FULL IVoteRepository)

Benefits of SRP:
- ReputationService changes if reputation rules change
- StatisticsService changes if calculation formulas change
- VoteManager changes if voting business logic changes
- They DON'T break each other when modified

Interface Segregation (I) in action:
- StatisticsService depends only on IVoteQuery (doesn't need voting methods)
- Each service gets only the dependencies it actually uses
"""

from core.base import IVoteQuery, IVoteRepository


class ReputationService:
    @staticmethod
    def apply_reputation_change(profile, points):
        if points != 0:
            profile.reputation_points += points
            profile.save()

class StatisticsService:
    def __init__(self, vote_query: IVoteQuery):
        self.vote_query = vote_query

    def calculate_popularity(self, obj):
        total_votes = len(self.vote_query.get_votes_for_object(obj))
        upvotes = len(self.vote_query.get_upvotes(obj))

        if total_votes == 0:
            return 0
        return (upvotes / total_votes) * 100


class VoteManager:
    def __init__(self, vote_repository: IVoteRepository):
        self.vote_repository = vote_repository

    def process_vote(self, obj, user, vote_type):
        return self.vote_repository.vote(obj, user, vote_type)

    def get_stats(self, obj):
        return {
            'total': len(self.vote_repository.get_votes_for_object(obj)),
            'count': self.vote_repository.get_vote_count(obj),
            'score': self.vote_repository.get_vote_score(obj),
        }