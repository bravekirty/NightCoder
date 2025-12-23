import django.urls
from core.rep_rules import REPUTATION_RULES
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, TemplateView

from users.forms import SignUpForm, UserProfileUpdateForm, UserUpdateForm

User = get_user_model()


class SignUpView(FormView):
    template_name = "users/signup.html"
    form_class = SignUpForm
    success_url = django.urls.reverse_lazy("users:login")

    def form_valid(self, form):
        new_user = form.save(commit=False)
        new_user.is_active = True
        new_user.save()
        return super().form_valid(form)


class UserLoginView(LoginView):
    def get_success_url(self):
        return django.urls.reverse("users:profile", kwargs={"username": self.request.user.username})


class PublicProfileView(DetailView):
    template_name = "users/public_profile.html"
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    context_object_name = "profile_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object

        context["questions_count"] = user.questions.count()
        context["answers_count"] = user.answers.count()
        context["reviews_count"] = user.reviews.count()
        context["accepted_answers"] = user.answers.filter(is_accepted=True).count()

        context["user_questions"] = (
            user.questions.select_related("author__profile").prefetch_related("answers").order_by("-created_at")[:10]
        )
        context["user_answers"] = user.answers.select_related(
            "question",
            "question__author",
            "author__profile",
        ).order_by("-created_at")[:10]
        context["user_reviews"] = user.reviews.select_related("author__profile").order_by("-created_at")[:10]

        question_upvotes = sum(len(question.get_upvotes()) for question in user.questions.all())
        answer_upvotes = sum(len(answer.get_upvotes()) for answer in user.answers.all())
        review_upvotes = sum(len(review.get_upvotes()) for review in user.reviews.all())
        accepted_answers = user.answers.filter(is_accepted=True).count()

        context["question_upvotes"] = question_upvotes * REPUTATION_RULES["question_upvote"]
        context["answer_upvotes"] = answer_upvotes * REPUTATION_RULES["answer_upvote"]
        context["review_upvotes"] = review_upvotes * REPUTATION_RULES["review_upvote"]
        context["accepted_points"] = accepted_answers * REPUTATION_RULES["answer_accepted"]

        context["total_earned"] = (
            context["question_upvotes"]
            + context["answer_upvotes"]
            + context["review_upvotes"]
            + context["accepted_points"]
        )

        context["is_owner"] = self.request.user == user
        return context


class ProfileUpdateView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile_edit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Initialize forms if not already in context (from POST)
        if "user_form" not in context:
            context["user_form"] = UserUpdateForm(instance=self.request.user)
        if "profile_form" not in context:
            context["profile_form"] = UserProfileUpdateForm(instance=self.request.user.profile)

        # Create a combined form object for template convenience
        class CombinedForm:
            def __init__(self, user_form, profile_form):
                self.user_form = user_form
                self.profile_form = profile_form

        context["form"] = CombinedForm(context["user_form"], context["profile_form"])
        return context

    def post(self, request, *args, **kwargs):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            # Use redirect instead of returning the URL string
            return redirect(self.get_success_url())

        # If forms are invalid, re-render with errors
        context = self.get_context_data(user_form=user_form, profile_form=profile_form)
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse("users:profile", kwargs={"username": self.request.user.username})
