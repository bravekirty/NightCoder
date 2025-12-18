import django.urls
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from forum.forms import AnswerForm, QuestionForm
from forum.models import Answer, Question


class QuestionListView(ListView):
    model = Question
    template_name = "forum/question_list.html"
    context_object_name = "questions"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("q", "").strip()

        if query:
            # Search logic
            words = query.split()
            q_objects = Q()

            for word in words:
                q_objects |= Q(title__icontains=word)
                q_objects |= Q(content__icontains=word)
                q_objects |= Q(answers__content__icontains=word)

            queryset = (
                Question.objects.filter(q_objects)
                .select_related("author", "author__profile")
                .prefetch_related("answers")
                .distinct()
            )
        else:
            queryset = Question.objects.all().select_related("author", "author__profile").prefetch_related("answers")

        self.search_words = queryset.count()
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()
        context["query"] = query
        context["results_count"] = self.search_words
        context["search_words"] = query.split()
        context["is_search"] = bool(query)

        return context


class QuestionDetailView(DetailView):
    model = Question
    template_name = "forum/question_detail.html"
    context_object_name = "question"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["answer_form"] = AnswerForm()
        context["answers"] = self.object.answers.all()
        question = context["question"]

        print(question.get_upvotes())
        question.upvotes = len(question.get_upvotes())
        question.downvotes = len(question.get_downvotes())
        question.vote_count = question.upvotes - question.downvotes

        question.user_vote = question.get_user_vote(self.request.user)

        for answer in context["answers"]:
            answer.upvotes = len(answer.get_upvotes())
            answer.downvotes = len(answer.get_downvotes())
            answer.vote_count = answer.upvotes - answer.downvotes

            answer.user_vote = answer.get_user_vote(self.request.user)

        return context


class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "forum/question_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class QuestionUpdateView(LoginRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = "forum/question_form.html"

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)


class QuestionDeleteView(LoginRequiredMixin, DeleteView):
    model = Question
    template_name = "forum/question_confirm_delete.html"

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)

    def get_success_url(self):
        return django.urls.reverse("forum:question_list")


class AnswerCreateView(LoginRequiredMixin, CreateView):
    model = Answer
    form_class = AnswerForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.question_id = self.kwargs["question_id"]
        return super().form_valid(form)

    def get_success_url(self):
        return django.urls.reverse("forum:question_detail", kwargs={"pk": self.kwargs["question_id"]})


class AnswerUpdateView(LoginRequiredMixin, UpdateView):
    model = Answer
    form_class = AnswerForm
    template_name = "forum/answer_form.html"

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)

    def get_success_url(self):
        return self.object.question.get_absolute_url()


class AnswerDeleteView(LoginRequiredMixin, DeleteView):
    model = Answer
    template_name = "forum/answer_confirm_delete.html"

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)

    def get_success_url(self):
        return self.object.question.get_absolute_url()


@require_POST
@login_required
def accept_answer(request, pk):
    answer = get_object_or_404(Answer, pk=pk)

    if request.user != answer.question.author:
        return JsonResponse({"error": _("Only question author can accept answers")}, status=403)

    Answer.objects.filter(question=answer.question, is_accepted=True).update(is_accepted=False)

    answer.mark_accepted()

    return JsonResponse({"success": True})
