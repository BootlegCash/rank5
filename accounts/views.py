# accounts/views.py

# --- Python Standard Library Imports ---
import calendar
import random
from datetime import date, datetime, timedelta

# --- Django Imports ---
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView

# --- Django Rest Framework (DRF) Imports ---
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

# --- Local Application Imports ---
from achievements.models import Achievement
from competitions.forms import CompetitionForm
from competitions.models import Competition, CompetitionParticipant
from .forms import (
    RegistrationForm,
    StatsUpdateForm,
    SendFriendRequestForm,
    PostForm,
    DailyLogForm,
)
from .models import Profile, FriendRequest, Post, DailyLog, current_log_date


# ==============================================================================
# --- TEMPLATE-BASED VIEWS (for rendering HTML pages) ---
# ==============================================================================

def register(request):
    if request.user.is_authenticated:
        return redirect('welcome')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('welcome')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('welcome')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        UserModel = get_user_model()
        if not UserModel.objects.filter(username=username).exists():
            messages.error(request, 'Account not found')
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('welcome')
            else:
                messages.error(request, 'Invalid password')
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('login')


@login_required
def profile(request):
    profile_obj = get_object_or_404(Profile, user=request.user)
    earned_achievements = profile_obj.check_achievements()
    return render(request, 'accounts/profile.html', {
        'profile': profile_obj,
        'achievements': earned_achievements,
    })


@login_required
def update_stats(request):
    profile = get_object_or_404(Profile, user=request.user)
    old_qualified = set(profile.check_achievements())

    if request.method == 'POST':
        form = StatsUpdateForm(request.POST)
        if form.is_valid():
            for field, increment in form.cleaned_data.items():
                setattr(profile, field, getattr(profile, field, 0) + increment)
            profile.save()

            log_date = current_log_date()
            daily_log, created = DailyLog.objects.get_or_create(
                profile=profile, date=log_date
            )
            for field, increment in form.cleaned_data.items():
                setattr(daily_log, field, getattr(daily_log, field, 0) + increment)
            daily_log.xp = daily_log.calculate_xp()
            daily_log.save()

            new_qualified = set(profile.check_achievements())
            just_unlocked = new_qualified - old_qualified
            for achievement in just_unlocked:
                profile.earned_achievements.add(achievement)
                messages.success(
                    request,
                    f'🎉 Congrats! You unlocked "{achievement.name}"!'
                )

            messages.success(request, 'Stats updated!')
            return redirect('profile')
    else:
        form = StatsUpdateForm()

    return render(request, 'accounts/update_stats.html', {'form': form})


@login_required
def leaderboard(request):
    profile_obj = get_object_or_404(Profile, user=request.user)
    friend_ids = profile_obj.friends.values_list('id', flat=True)
    profiles = Profile.objects.filter(
        Q(id__in=friend_ids) | Q(id=profile_obj.id)
    ).order_by('-xp')
    return render(request, 'accounts/leaderboard.html', {
        'profiles': profiles,
        'user_profile': profile_obj
    })


@login_required
def friend_list(request):
    profile_obj = get_object_or_404(Profile, user=request.user)
    received_requests = FriendRequest.objects.filter(to_user=profile_obj, accepted=False)
    sent_requests = FriendRequest.objects.filter(from_user=profile_obj, accepted=False)

    return render(request, 'accounts/friend_list.html', {
        'friends': profile_obj.friends.all(),
        'received_requests': received_requests,
        'sent_requests': sent_requests,
    })


@login_required
def send_friend_request(request):
    if request.method == 'POST':
        form = SendFriendRequestForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                to_user_profile = User.objects.get(username=username).profile
                if to_user_profile == request.user.profile:
                    messages.error(request, "You can't send a request to yourself")
                elif FriendRequest.objects.filter(
                    from_user=request.user.profile, to_user=to_user_profile
                ).exists():
                    messages.error(request, "Friend request already sent")
                elif to_user_profile in request.user.profile.friends.all():
                    messages.error(request, "You're already friends")
                else:
                    FriendRequest.objects.create(
                        from_user=request.user.profile,
                        to_user=to_user_profile
                    )
                    messages.success(request, 'Friend request sent!')
            except User.DoesNotExist:
                messages.error(request, 'User not found')
            return redirect('friend_list')
    else:
        form = SendFriendRequestForm()

    return render(request, 'accounts/send_friend_request.html', {'form': form})


@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user.profile)
    try:
        friend_request.accept()
        messages.success(request, f"You're now friends with {friend_request.from_user.user.username}!")
    except Exception as e:
        messages.error(request, f"Error accepting request: {str(e)}")
    return redirect('friend_list')


@login_required
def reject_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user.profile)
    friend_request.delete()
    messages.success(request, "Friend request rejected")
    return redirect('friend_list')


@login_required
@require_POST
def remove_friend(request, profile_id):
    friend_profile_obj = get_object_or_404(Profile, id=profile_id)
    if friend_profile_obj in request.user.profile.friends.all():
        request.user.profile.friends.remove(friend_profile_obj)
        friend_profile_obj.friends.remove(request.user.profile)
        messages.success(request, f"You have removed {friend_profile_obj.user.username} from your friends.")
    else:
        messages.error(request, "This user is not in your friend list.")
    return redirect('friend_list')


@login_required
def welcome(request):
    friend_posts = Post.objects.filter(user__in=request.user.profile.friends.all()).order_by('-created_at')
    user_posts = Post.objects.filter(user=request.user.profile).order_by('-created_at')
    all_posts = (friend_posts | user_posts).distinct().order_by('-created_at')
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user.profile
            post.save()
            return redirect('welcome')
    else:
        form = PostForm()
    return render(request, 'accounts/welcome.html', {'posts': all_posts, 'form': form})


@require_POST
@login_required
def like_post(request, post_id):
    post_obj = get_object_or_404(Post, id=post_id)
    profile_obj = request.user.profile
    if profile_obj in post_obj.likes.all():
        post_obj.likes.remove(profile_obj)
        liked = False
    else:
        post_obj.likes.add(profile_obj)
        liked = True
    return JsonResponse({
        'liked': liked,
        'like_count': post_obj.likes.count()
    })


class CreatePostView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'accounts/compose_post.html'
    success_url = reverse_lazy('welcome')

    def form_valid(self, form):
        form.instance.user = self.request.user.profile
        return super().form_valid(form)


def safety_guidelines(request):
    return render(request, 'accounts/safety_guidelines.html')


@login_required
def about(request):
    return render(request, 'accounts/about.html')


@login_required
def achievements(request):
    profile_obj = request.user.profile
    all_achievements = Achievement.objects.all()
    earned = profile_obj.check_achievements()

    progress_requirements = {
        "BEER_BEGINNER": ("beer", 10),
        "WHISKEY_WARRIOR": ("whiskey", 25),
        "RUM_RUNNER": ("rum", 20),
    }

    post_count = Post.objects.filter(user=profile_obj).count()

    achievements_list = []
    for achievement in all_achievements:
        is_earned = achievement in earned
        progress = 0
        if achievement.code in progress_requirements:
            attr, target = progress_requirements[achievement.code]
            if attr == "friends":
                value = profile_obj.friends.count()
            elif attr == "post_count":
                value = post_count
            else:
                value = getattr(profile_obj, attr, 0)
            progress = min(100, int((value / target) * 100))
        else:
            progress = 100 if is_earned else 0

        achievements_list.append({
            'achievement': achievement,
            'is_earned': is_earned,
            'progress': progress
        })

    return render(request, 'accounts/achievements.html', {
        'achievements_list': achievements_list
    })


@login_required
def friend_search(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = Profile.objects.filter(
            user__username__icontains=query
        ).exclude(user=request.user)[:5]
    return render(request, 'accounts/friend_search.html', {
        'query': query,
        'results': results
    })


@login_required
def friend_profile(request, username):
    friend_profile_obj = get_object_or_404(Profile, user__username=username)
    is_friend = friend_profile_obj in request.user.profile.friends.all()
    earned_achievements = friend_profile_obj.check_achievements()
    
    return render(request, 'accounts/friend_profile.html', {
        'friend_profile': friend_profile_obj,
        'is_friend': is_friend,
        'achievements': earned_achievements,
    })


@login_required
def update_daily_log(request):
    profile = get_object_or_404(Profile, user=request.user)
    log_date = current_log_date()
    daily_log, created = DailyLog.objects.get_or_create(profile=profile, date=log_date)
    
    if request.method == "POST":
        form = DailyLogForm(request.POST)
        if form.is_valid():
            for field, increment in form.cleaned_data.items():
                if increment and increment > 0:
                    current_val = getattr(daily_log, field, 0)
                    setattr(daily_log, field, current_val + increment)
            
            daily_log.xp = daily_log.calculate_xp()
            daily_log.save()
            
            messages.success(request, "Today's log has been updated!")
            return redirect('profile')
    else:
        form = DailyLogForm()
    
    return render(request, "accounts/update_daily_log.html", {"form": form, "daily_log": daily_log})


@login_required
def daily_log_calendar(request):
    profile = get_object_or_404(Profile, user=request.user)
    logs = profile.daily_logs.all()
    return render(request, "accounts/daily_log_calendar.html", {"logs": logs})


@login_required
def monthly_calendar(request, year=None, month=None):
    profile = get_object_or_404(Profile, user=request.user)
    
    now = timezone.localtime(timezone.now())
    today = now.date()
    
    year = int(year) if year else today.year
    month = int(month) if month else today.month

    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)

    logs_for_month = DailyLog.objects.filter(
        profile=profile,
        date__gte=first_day.date(),
        date__lte=last_day.date()
    )
    
    cal = calendar.Calendar(firstweekday=6)
    month_weeks = []
    for week in cal.monthdatescalendar(year, month):
        week_days = []
        for day in week:
            log = next((l for l in logs_for_month if l.date == day), None)
            week_days.append({
                'date': day,
                'day': day.day,
                'is_current_month': day.month == month,
                'is_today': day == today,
                'log': log
            })
        month_weeks.append(week_days)

    prev_month_date = first_day - timedelta(days=1)
    next_month_date = last_day + timedelta(days=1)

    context = {
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'weeks': month_weeks,
        'today': today,
        'prev_year': prev_month_date.year,
        'prev_month': prev_month_date.month,
        'next_year': next_month_date.year,
        'next_month': next_month_date.month,
    }
    return render(request, "accounts/monthly_calendar.html", context)


@login_required
def day_log_detail(request, year, month, day):
    profile = get_object_or_404(Profile, user=request.user)
    try:
        log_date = date(year, month, day)
    except ValueError:
        return render(request, 'accounts/day_log_detail.html', {'error': 'Invalid date'})

    daily_log = DailyLog.objects.filter(profile=profile, date=log_date).first()
    return render(request, 'accounts/day_log_detail.html', {
        'log_date': log_date,
        'daily_log': daily_log,
    })


@login_required
def competition_list(request):
    profile = request.user.profile
    created = profile.created_competitions.all()
    joined = profile.competitions.exclude(created_by=profile)
    return render(request, 'competitions/competition_list.html',{
        'created': created, 'joined': joined
    })


@login_required
def competition_detail(request, pk):
    comp = get_object_or_404(Competition, pk=pk)
    board = comp.leaderboard()
    return render(request, 'competitions/competition_detail.html',{
        'competition': comp, 'leaderboard': board
    })


@login_required
def competition_create(request):
    if request.method == 'POST':
        form = CompetitionForm(request.POST, user_profile=request.user.profile)
        if form.is_valid():
            comp = form.save(commit=False)
            comp.created_by = request.user.profile
            comp.save()
            form.save_m2m()
            comp.participants.add(request.user.profile)
            return redirect('competitions:competition_detail', pk=comp.pk)
    else:
        form = CompetitionForm(user_profile=request.user.profile)

    return render(request, 'competitions/competition_create.html', {
        'form': form
    })



# ==============================================================================
# --- API VIEWS (for your Flutter App) ---
# ==============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user_api(request):
    """
    API endpoint for user registration from the Flutter app.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.data)
        if form.is_valid():
            user = form.save()
            return Response(
                {
                    "message": "User registered successfully.",
                    "username": user.username,
                    "email": user.email
                },
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response({"error": "This endpoint only supports POST requests."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    print(f"--- API: Attempting to fetch profile for user: {user.username} (ID: {user.id}) ---")

    try:
        profile = user.profile
        print(f"--- API: Profile found for user: {user.username} ---")

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": profile.display_name,
            "xp": profile.xp,
            "rank": profile.rank,
            "total_alcohol": profile.total_alcohol,
        })
    except Profile.DoesNotExist:
        print(f"--- API ERROR: Profile.DoesNotExist for user: {user.username} ---")
        return Response(
            {"error": "Profile not found for this user. The creation process failed."},
            status=status.HTTP_404_NOT_FOUND
        )
