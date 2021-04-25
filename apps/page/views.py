from django.shortcuts import render
from apps.document.models import Document


def index(request):
    if not request.user.is_authenticated:
        return render(request, 'page/index.html')

    context = {
        "account_documents": Document.objects.filter(account=request.user.account).count(),
        "user_documents": Document.objects.filter(user=request.user).count(),
    }

    return render(request, 'page/home.html', context)
