"""Request validation and response shapes for the café API."""
from collections.abc import Sequence

from rest_framework import serializers

from .models import Game, Player, Session


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = [
            "id",
            "title",
            "min_players",
            "max_players",
            "playtime_minutes",
            "difficulty",
            "created_at",
        ]

    def validate(self, attrs: dict) -> dict:
        min_players: int = attrs.get("min_players", getattr(self.instance, "min_players", 0))
        max_players: int = attrs.get("max_players", getattr(self.instance, "max_players", 0))
        if min_players > max_players:
            raise serializers.ValidationError(
                {"max_players": "max_players must be greater than or equal to min_players."}
            )
        return attrs


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ["id", "nickname", "email", "joined_at"]


def player_count_error(game: Game, player_count: int) -> str | None:
    """Return why `player_count` does not fit `game`, or None when it fits."""
    if game.min_players <= player_count <= game.max_players:
        return None
    return (
        f"'{game.title}' needs {game.min_players}-{game.max_players} players, "
        f"got {player_count}."
    )


class SessionSerializer(serializers.ModelSerializer):
    game_title = serializers.CharField(source="game.title", read_only=True)
    players = serializers.PrimaryKeyRelatedField(many=True, queryset=Player.objects.all())

    class Meta:
        model = Session
        fields = ["id", "game", "game_title", "table_number", "started_at", "players", "notes"]

    def validate_players(self, players: Sequence[Player]) -> Sequence[Player]:
        if len({player.pk for player in players}) != len(players):
            raise serializers.ValidationError("A player cannot be listed twice.")
        return players

    def validate(self, attrs: dict) -> dict:
        is_roster_changing = "game" in attrs or "players" in attrs
        if not is_roster_changing:
            return attrs
        game = attrs.get("game", getattr(self.instance, "game", None))
        player_count = (
            len(attrs["players"]) if "players" in attrs else self.instance.players.count()
        )
        error = player_count_error(game, player_count)
        if error:
            raise serializers.ValidationError({"players": error})
        return attrs


class AddPlayerSerializer(serializers.Serializer):
    """Body of POST /sessions/{id}/players/ — seats one more player."""

    player_id = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())

    def validate_player_id(self, player: Player) -> Player:
        session: Session = self.context["session"]
        if session.players.filter(pk=player.pk).exists():
            raise serializers.ValidationError("Player is already in this session.")
        if session.players.count() >= session.game.max_players:
            raise serializers.ValidationError(
                f"Session is full: '{session.game.title}' allows {session.game.max_players} players."
            )
        return player
