from django.shortcuts import render

from notifications.services import notify_support_ticket_created

from .forms import SupportQuestionForm


def ask_question(request):
    if request.method == "POST":
        form = SupportQuestionForm(request.POST)
        if form.is_valid():
            ticket = form.save()
            notify_support_ticket_created(ticket)
            return render(request, "support/question_success.html", {"ticket": ticket})
    else:
        form = SupportQuestionForm()

    return render(request, "support/question_form.html", {"form": form})
