import random
from django.shortcuts import render, redirect
from django.db import connection


def index(request):
    """
    Root route: picks a random number if none exists in session,
    then displays the guessing form.
    """
    # Only generate a new number if one doesn't exist in session
    if 'secret_number' not in request.session:
        request.session['secret_number'] = random.randint(1, 100)
        request.session['attempts'] = 0  # Ninja Bonus: track attempts

    context = {
        'message': request.session.get('message', None),
        'status': request.session.get('status', None),       # 'low', 'high', 'correct', 'lose'
        'attempts': request.session.get('attempts', 0),
        'game_over': request.session.get('game_over', False),
        'secret_number': request.session.get('secret_number') if request.session.get('game_over') else None,
    }

    # Clear per-guess message after reading it
    if 'message' in request.session:
        del request.session['message']

    return render(request, 'great_number_game_app/index.html', context)


def guess(request):
    """
    POST route: checks the submitted guess against the session number.
    """
    if request.method == 'POST':
        try:
            user_guess = int(request.POST.get('guess'))
        except (ValueError, TypeError):
            request.session['message'] = "Please enter a valid number!"
            request.session['status'] = 'error'
            return redirect('index')

        secret = request.session.get('secret_number')
        attempts = request.session.get('attempts', 0)

        # SENSEI BONUS: Limit to 5 attempts
        MAX_ATTEMPTS = 5
        attempts += 1
        request.session['attempts'] = attempts

        if user_guess < secret:
            request.session['message'] = "Too low!"
            request.session['status'] = 'low'
        elif user_guess > secret:
            request.session['message'] = "Too high!"
            request.session['status'] = 'high'
        else:
            # Correct!
            request.session['message'] = f"{secret} was the number!"
            request.session['status'] = 'correct'
            request.session['game_over'] = True

            # SENSEI BONUS: Save winner to leaderboard DB
            save_winner(request.session.get('player_name', 'Anonymous'), attempts)

        # SENSEI BONUS: out of attempts
        if attempts >= MAX_ATTEMPTS and request.session.get('status') != 'correct':
            request.session['message'] = f"You Lose! The number was {secret}."
            request.session['status'] = 'lose'
            request.session['game_over'] = True

    return redirect('index')


def reset(request):
    """Clears the session and restarts the game."""
    request.session.flush()
    return redirect('index')


def submit_name(request):
    """SENSEI BONUS: Save winner name after a correct guess."""
    if request.method == 'POST':
        name = request.POST.get('name', 'Anonymous').strip() or 'Anonymous'
        attempts = request.session.get('attempts', 0)
        save_winner(name, attempts)
        request.session['player_name'] = name
    return redirect('leaderboard')


def leaderboard(request):
    """SENSEI BONUS: Display leaderboard of winners."""
    winners = get_winners()
    return render(request, 'great_number_game_app/leaderboard.html', {'winners': winners})


# ── Database helpers for leaderboard ──────────────────────────────────────────

def create_table():
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS winners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                attempts INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_winner(name, attempts):
    create_table()
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO winners (name, attempts) VALUES (%s, %s)",
            [name, attempts]
        )


def get_winners():
    create_table()
    with connection.cursor() as cursor:
        cursor.execute("SELECT name, attempts, created_at FROM winners ORDER BY attempts ASC, created_at ASC")
        rows = cursor.fetchall()
    return [{'name': r[0], 'attempts': r[1], 'date': r[2]} for r in rows]
