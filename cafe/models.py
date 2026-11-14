"""Board game café domain: games on the shelf, players, and play sessions."""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

MIN_PLAYERS_ALLOWED = 1
MAX_PLAYERS_ALLOWED = 20
MAX_TABLE_NUMBER = 50


class Difficulty(models.TextChoices):
    EASY = "easy", "Easy"
    MEDIUM = "medium", "Medium"
    HARD = "hard", "Hard"


class Game(models.Model):
    """A board game the café owns."""

    title = models.CharField(max_length=120, unique=True)
    min_players = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_PLAYERS_ALLOWED), MaxValueValidator(MAX_PLAYERS_ALLOWED)]
    )
    max_players = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_PLAYERS_ALLOWED), MaxValueValidator(MAX_PLAYERS_ALLOWED)]
    )
    playtime_minutes = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class Player(models.Model):
    """A café visitor who joins play sessions."""

    nickname = models.CharField(max_length=40, unique=True)
    email = models.EmailField(unique=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nickname"]

    def __str__(self) -> str:
        return self.nickname


class Session(models.Model):
    """One sitting of a game at a café table.

    Game -> Session is one-to-many; Session <-> Player is many-to-many.
    """

    game = models.ForeignKey(Game, on_delete=models.PROTECT, related_name="sessions")
    players = models.ManyToManyField(Player, related_name="sessions")
    table_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(MAX_TABLE_NUMBER)]
    )
    started_at = models.DateTimeField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.game} at table {self.table_number}"
