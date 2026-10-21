import random
from django.conf import settings
from django.db import models


def generate_target() -> int:
    return random.randint(1, 100)


def generate_target_for_range(max_val: int = 100) -> int:
    return random.randint(1, max_val)



class GuessGame(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Oson (1-50)'),
        ('medium', 'O\'rtacha (1-100)'),
        ('hard', 'Qiyin (1-200)'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='guess_games'
    )
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    max_range = models.IntegerField(default=100)
    max_attempts = models.IntegerField(null=True, blank=True)  # e.g., 7 for hard mode
    target = models.IntegerField(default=1)
    attempts = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_won = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    duration_seconds = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk and (not self.target or self.target == 1):
            if self.difficulty == 'easy':
                self.max_range = 50
                self.max_attempts = None
            elif self.difficulty == 'hard':
                self.max_range = 200
                self.max_attempts = 7
            else:
                self.difficulty = 'medium'
                self.max_range = 100
                self.max_attempts = None
            self.target = random.randint(1, self.max_range)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        status = "Won" if self.is_won else ("Active" if self.is_active else "Lost")
        return f"Game #{self.id} ({self.difficulty}) for {self.user.username} ({status}, Attempts: {self.attempts})"
