# competitions/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Competition
from .forms import CompetitionForm

@login_required
def competition_list(request):
    """
    Display your competitions, optionally filtering by status.
    Newest (by start date) appear first courtesy of Competition.Meta.ordering.
    """
    status = request.GET.get('status')
    qs = Competition.objects.filter(created_by=request.user.profile)

    if status == 'ongoing':
        qs = qs.filter(is_active=True)
    elif status == 'ended':
        qs = qs.filter(is_active=False)

    return render(request, 'competitions/competition_list.html', {
        'created': qs,
        'status': status,
    })


@login_required
def competition_create(request):
    """
    Create a new competition. Invites (M2M) from form and auto-adds creator.
    """
    if request.method == 'POST':
        form = CompetitionForm(request.POST, user_profile=request.user.profile)
        if form.is_valid():
            comp = form.save(commit=False)
            comp.created_by = request.user.profile
            comp.save()
            form.save_m2m()
            comp.participants.add(request.user.profile)
            messages.success(request, f'Competition "{comp.name}" created!')
            return redirect('competitions:competition_detail', pk=comp.pk)
    else:
        form = CompetitionForm(user_profile=request.user.profile)

    return render(request, 'competitions/competition_create.html', {
        'form': form
    })

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Competition

@login_required
def competition_detail(request, pk):
    comp = get_object_or_404(Competition, pk=pk)
    board = comp.leaderboard()
    return render(request, 'competitions/competition_detail.html', {
        'competition': comp,
        'leaderboard':  board,
    })


@login_required
def delete_competition(request, pk):
    """
    Delete an ended competition. Only the creator may delete.
    """
    comp = get_object_or_404(
        Competition,
        pk=pk,
        created_by=request.user.profile
    )
    if request.method == 'POST':
        name = comp.name
        comp.delete()
        messages.success(request, f'Competition "{name}" was deleted.')
        return redirect('competitions:competition_list')

    # On GET (or others), just redirect back to the list
    return redirect('competitions:competition_list')
