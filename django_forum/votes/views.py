from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST


@login_required
@require_POST
def vote(request, content_type_id, object_id, vote_type):
    if vote_type not in ["up", "down"]:
        return JsonResponse({"error": _("Invalid vote type")}, status=400)

    content_type = get_object_or_404(ContentType, id=content_type_id)
    model_class = content_type.model_class()
    obj = get_object_or_404(model_class, id=object_id)

    if hasattr(obj, "author") and obj.author == request.user:
        return JsonResponse({"error": _("Cannot vote on your own content")}, status=400)

    result = obj.vote(request.user, vote_type)

    return JsonResponse(
        {
            "success": True,
            "result": result,
            "vote_count": obj.get_vote_score(),
            "user_vote": obj.get_user_vote(request.user),
            "upvotes": len(obj.get_upvotes()),
            "downvotes": len(obj.get_downvotes()),
        },
    )
