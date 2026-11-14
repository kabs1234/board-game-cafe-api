"""API endpoints: CRUD for each model plus nested related-data routes."""
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Game, Player, Session
from .serializers import (
    AddPlayerSerializer,
    GameSerializer,
    PlayerSerializer,
    SessionSerializer,
)

SESSIONS_WITH_RELATIONS = Session.objects.select_related("game").prefetch_related("players")


class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer

    @action(detail=True, methods=["get"])
    def sessions(self, request: Request, pk: str) -> Response:
        """GET /games/{id}/sessions/ — every session played with this game."""
        game = self.get_object()
        serializer = SessionSerializer(SESSIONS_WITH_RELATIONS.filter(game=game), many=True)
        return Response(serializer.data)


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

    @action(detail=True, methods=["get"])
    def sessions(self, request: Request, pk: str) -> Response:
        """GET /players/{id}/sessions/ — every session this player joined."""
        player = self.get_object()
        serializer = SessionSerializer(SESSIONS_WITH_RELATIONS.filter(players=player), many=True)
        return Response(serializer.data)


class SessionViewSet(viewsets.ModelViewSet):
    queryset = SESSIONS_WITH_RELATIONS
    serializer_class = SessionSerializer

    @action(detail=True, methods=["get"], url_path="players")
    def list_players(self, request: Request, pk: str) -> Response:
        """GET /sessions/{id}/players/ — players seated at this session."""
        session = self.get_object()
        return Response(PlayerSerializer(session.players.all(), many=True).data)

    @list_players.mapping.post
    def add_player(self, request: Request, pk: str) -> Response:
        """POST /sessions/{id}/players/ — seat one more player."""
        session = self.get_object()
        serializer = AddPlayerSerializer(data=request.data, context={"session": session})
        serializer.is_valid(raise_exception=True)
        session.players.add(serializer.validated_data["player_id"])
        return Response(SessionSerializer(session).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"players/(?P<player_id>\d+)")
    def remove_player(self, request: Request, pk: str, player_id: str) -> Response:
        """DELETE /sessions/{id}/players/{player_id}/ — a player leaves the table."""
        session = self.get_object()
        player = get_object_or_404(session.players, pk=player_id)
        session.players.remove(player)
        return Response(status=status.HTTP_204_NO_CONTENT)
