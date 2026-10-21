import json
from django.test import TestCase
from django.contrib.auth.models import User
from games.models import GuessGame


class GameTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='player', password='Password123!')
        self.client.login(username='player', password='Password123!')

    def test_index_creates_game_session(self):
        self.assertEqual(GuessGame.objects.filter(user=self.user, is_active=True).count(), 0)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(GuessGame.objects.filter(user=self.user, is_active=True).count(), 1)
        game = GuessGame.objects.get(user=self.user, is_active=True)
        self.assertTrue(1 <= game.target <= 100)
        self.assertEqual(game.attempts, 0)

    def test_index_resumes_existing_game(self):
        game = GuessGame.objects.create(user=self.user, target=42, attempts=3)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '3')
        self.assertEqual(GuessGame.objects.filter(user=self.user, is_active=True).count(), 1)
        self.assertEqual(GuessGame.objects.get(user=self.user, is_active=True).id, game.id)

    def test_guess_api_low_high_win_and_temperature(self):
        game = GuessGame.objects.create(user=self.user, target=50, max_range=100)

        # Guess too low (diff 25 -> cold)
        res_low = self.client.post(
            '/api/guess/',
            data=json.dumps({'guess': 25, 'duration_seconds': 5}),
            content_type='application/json'
        )
        self.assertEqual(res_low.status_code, 200)
        data_low = res_low.json()
        self.assertEqual(data_low['status'], 'low')
        self.assertEqual(data_low['message'], 'Juda kichik!')
        self.assertEqual(data_low['temp'], 'cold')
        self.assertEqual(data_low['attempts'], 1)

        # Guess too high (diff 2 -> boiling)
        res_high = self.client.post(
            '/api/guess/',
            data=json.dumps({'guess': 52, 'duration_seconds': 8}),
            content_type='application/json'
        )
        self.assertEqual(res_high.status_code, 200)
        data_high = res_high.json()
        self.assertEqual(data_high['status'], 'high')
        self.assertEqual(data_high['message'], 'Juda katta!')
        self.assertEqual(data_high['temp'], 'boiling')
        self.assertEqual(data_high['attempts'], 2)

        # Winning guess
        res_win = self.client.post(
            '/api/guess/',
            data=json.dumps({'guess': 50, 'duration_seconds': 10}),
            content_type='application/json'
        )
        self.assertEqual(res_win.status_code, 200)
        data_win = res_win.json()
        self.assertEqual(data_win['status'], 'win')
        self.assertEqual(data_win['message'], "To'g'ri! Siz yutdingiz!")
        self.assertEqual(data_win['attempts'], 3)
        self.assertTrue(data_win['score'] > 0)

        game.refresh_from_db()
        self.assertFalse(game.is_active)
        self.assertTrue(game.is_won)
        self.assertEqual(game.attempts, 3)

    def test_hard_mode_max_attempts_exceeded(self):
        game = GuessGame.objects.create(user=self.user, target=80, difficulty='hard', max_attempts=2, max_range=200)
        self.client.post('/api/guess/', data=json.dumps({'guess': 20}), content_type='application/json')
        res_lost = self.client.post('/api/guess/', data=json.dumps({'guess': 30}), content_type='application/json')
        self.assertEqual(res_lost.status_code, 200)
        data = res_lost.json()
        self.assertEqual(data['status'], 'lost')
        game.refresh_from_db()
        self.assertFalse(game.is_active)
        self.assertFalse(game.is_won)

    def test_reset_api_with_difficulty(self):
        GuessGame.objects.create(user=self.user, target=50, attempts=5, is_active=True)
        res = self.client.post(
            '/api/reset/',
            data=json.dumps({'difficulty': 'hard'}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'reset')
        self.assertEqual(data['difficulty'], 'hard')
        self.assertEqual(data['max_range'], 200)
        self.assertEqual(data['max_attempts'], 7)

    def test_leaderboard_api(self):
        GuessGame.objects.create(user=self.user, target=50, attempts=2, is_active=False, is_won=True, score=850)
        res = self.client.get('/api/leaderboard/')
        self.assertEqual(res.status_code, 200)
        leaders = res.json().get('leaderboard', [])
        self.assertTrue(len(leaders) >= 1)
        self.assertEqual(leaders[0]['username'], 'player')
        self.assertEqual(leaders[0]['score'], 850)
