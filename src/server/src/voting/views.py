from django.shortcuts import render


def index(request):
    if request.htmx:
        template_name = "voting/landing/content.html"
    else:
        template_name = "voting/landing/index.html"
    return render(request, template_name)
