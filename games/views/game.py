import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.db.models import Min, Max
from games.models import GuessGame


def get_temperature(diff: int) -> dict:
    if diff <= 3:
        return {'temp': 'boiling', 'temp_label': 'Qaynoq! 🔥'}
    elif diff <= 10:
        return {'temp': 'warm', 'temp_label': 'Issiq! ☀️'}
    elif diff <= 20:
        return {'temp': 'lukewarm', 'temp_label': 'Iliq 🌤️'}
    return {'temp': 'cold', 'temp_label': 'Sovuq ❄️'}


@login_required
def index_view(request: HttpRequest) -> HttpResponse:
    game = GuessGame.objects.filter(user=request.user, is_active=True).first()
    if not game:
        game = GuessGame.objects.create(user=request.user, difficulty='medium')

    user_best = GuessGame.objects.filter(user=request.user, is_won=True).aggregate(
        best_attempts=Min('attempts'),
        best_score=Max('score')
    )

    top_games = GuessGame.objects.filter(is_won=True).select_related('user').order_by('-score', 'attempts', 'duration_seconds')[:5]

    return render(request, 'games/game.html', {
        'game': game,
        'user_best': user_best,
        'top_games': top_games,
    })


@login_required
@require_POST
def guess_api(request: HttpRequest) -> JsonResponse:
    try:
        data = json.loads(request.body.decode('utf-8'))
        guess = data.get('guess')
        duration = data.get('duration_seconds', 0)
        if not isinstance(duration, int) or duration < 0:
            duration = 0
        if guess is None or not isinstance(guess, int) or isinstance(guess, bool):
            return JsonResponse({'error': 'Noto\'g\'ri format.'}, status=400)
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
        return JsonResponse({'error': 'JSON ma\'lumoti noto\'g\'ri.'}, status=400)

    game = GuessGame.objects.filter(user=request.user, is_active=True).first()
    if not game:
        game = GuessGame.objects.create(user=request.user, difficulty='medium')

    if not (1 <= guess <= game.max_range):
        return JsonResponse({
            'error': f'Noto\'g\'ri son. 1 dan {game.max_range} gacha butun son kiriting.'
        }, status=400)

    game.attempts += 1
    game.duration_seconds = duration
    diff = abs(guess - game.target)
    temp_info = get_temperature(diff)

    if guess < game.target:
        # Check hard mode limit
        if game.max_attempts and game.attempts >= game.max_attempts:
            game.is_active = False
            game.is_won = False
            game.save()
            return JsonResponse({
                'status': 'lost',
                'message': f'Imkoniyatlar tugadi! Yashirin son: {game.target}',
                'attempts': game.attempts,
                'target': game.target,
                **temp_info
            })

        game.save(update_fields=['attempts', 'duration_seconds'])
        return JsonResponse({
            'status': 'low',
            'message': 'Juda kichik!',
            'attempts': game.attempts,
            'max_attempts': game.max_attempts,
            **temp_info
        })

    elif guess > game.target:
        # Check hard mode limit
        if game.max_attempts and game.attempts >= game.max_attempts:
            game.is_active = False
            game.is_won = False
            game.save()
            return JsonResponse({
                'status': 'lost',
                'message': f'Imkoniyatlar tugadi! Yashirin son: {game.target}',
                'attempts': game.attempts,
                'target': game.target,
                **temp_info
            })

        game.save(update_fields=['attempts', 'duration_seconds'])
        return JsonResponse({
            'status': 'high',
            'message': 'Juda katta!',
            'attempts': game.attempts,
            'max_attempts': game.max_attempts,
            **temp_info
        })

    else:
        # Won!
        game.is_active = False
        game.is_won = True
        base_score = 1000 if game.difficulty == 'easy' else (1500 if game.difficulty == 'medium' else 2500)
        calculated_score = max(50, base_score - (game.attempts * 60) - (duration * 5))
        game.score = calculated_score
        game.save(update_fields=['attempts', 'is_active', 'is_won', 'score', 'duration_seconds'])
        return JsonResponse({
            'status': 'win',
            'message': "To'g'ri! Siz yutdingiz!",
            'attempts': game.attempts,
            'score': game.score,
            'duration_seconds': game.duration_seconds,
            'temp': 'boiling',
            'temp_label': 'Topildi! 🎯'
        })


@login_required
@require_POST
def reset_api(request: HttpRequest) -> JsonResponse:
    difficulty = 'medium'
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
        req_diff = data.get('difficulty')
        if req_diff in ['easy', 'medium', 'hard']:
            difficulty = req_diff
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    GuessGame.objects.filter(user=request.user, is_active=True).update(is_active=False)
    new_game = GuessGame.objects.create(user=request.user, difficulty=difficulty)

    return JsonResponse({
        'status': 'reset',
        'attempts': 0,
        'difficulty': new_game.difficulty,
        'max_range': new_game.max_range,
        'max_attempts': new_game.max_attempts,
    })


@login_required
def leaderboard_api(request: HttpRequest) -> JsonResponse:
    top_games = GuessGame.objects.filter(is_won=True).select_related('user').order_by('-score', 'attempts')[:10]
    data = [
        {
            'username': g.user.username,
            'difficulty': g.difficulty,
            'attempts': g.attempts,
            'score': g.score,
            'duration': g.duration_seconds,
        }
        for g in top_games
    ]
    return JsonResponse({'leaderboard': data})
