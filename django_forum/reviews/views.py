import django.urls
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from reviews.forms import CourseReviewForm
from reviews.models import CourseReview


class ReviewListView(ListView):
    model = CourseReview
    template_name = "reviews/review_list.html"
    context_object_name = "reviews"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("q", "").strip()

        if query:
            queryset = (
                CourseReview.objects.filter(
                    Q(course_name__icontains=query) | Q(title__icontains=query) | Q(content__icontains=query),
                )
                .select_related("author", "author__profile")
                .distinct()
            )
        else:
            queryset = CourseReview.objects.all().select_related("author", "author__profile")

        self.search_words = queryset.count()
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()
        context["query"] = query
        context["results_count"] = self.search_words
        context["is_search"] = bool(query)

        for review in context["reviews"]:
            review.upvotes = len(review.get_upvotes())
            review.downvotes = len(review.get_downvotes())
            review.vote_count = review.upvotes - review.downvotes

        return context


class ReviewDetailView(DetailView):
    model = CourseReview
    template_name = "reviews/review_detail.html"
    context_object_name = "review"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review = context["review"]

        # Add vote data
        review.upvotes = len(review.get_upvotes())
        review.downvotes = len(review.get_downvotes())
        review.vote_count = review.upvotes - review.downvotes

        if self.request.user.is_authenticated:
            review.user_vote = review.get_user_vote(self.request.user)
        else:
            review.user_vote = None

        return context


class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = CourseReview
    form_class = CourseReviewForm
    template_name = "reviews/review_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = CourseReview
    form_class = CourseReviewForm
    template_name = "reviews/review_form.html"

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    model = CourseReview
    template_name = "reviews/review_confirm_delete.html"
    context_object_name = "review"

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)

    def get_success_url(self):
        return django.urls.reverse("reviews:review_list")


class UserReviewListView(ListView):
    template_name = "reviews/user_reviews.html"
    context_object_name = "reviews"
    paginate_by = 10

    def get_queryset(self):
        username = self.kwargs["username"]
        return CourseReview.objects.filter(author__username=username).select_related("author", "author__profile")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reviews = self.get_queryset()
        context["profile_user"] = reviews.first().author if reviews else None
        print(context["profile_user"])

        for review in context["reviews"]:
            review.upvotes = review.get_upvotes().count()
            review.downvotes = review.get_downvotes().count()
            review.vote_count = review.upvotes - review.downvotes

        if reviews:
            total_rating = sum(review.rating for review in reviews)
            context["average_rating"] = round(total_rating / len(reviews), 1)

        return context
