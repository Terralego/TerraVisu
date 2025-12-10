from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseForbidden


@login_required
def serve_private_files(request, path):
    file_path = settings.PRIVATE_MEDIA_ROOT / path
    if not file_path.exists():
        raise Http404()
    if not (
        request.user.is_report_manager
        or request.user.is_declaration_manager
        or request.user.is_superuser
    ):
        return HttpResponseForbidden()
    response = HttpResponse()
    response["X-Accel-Redirect"] = f"/private_files/media/{path}"
    response["Content-Type"] = ""  # Let nginx determine
    return response
