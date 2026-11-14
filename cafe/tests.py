"""End-to-end tests for every endpoint and the main error paths."""
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Difficulty, Game, Player, Session

STARTED_AT = "2026-11-14T18:00:00Z"


class CafeApiTestCase(APITestCase):
    def setUp(self) -> None:
        self.game = Game.objects.create(
            title="Catan",
            min_players=2,
            max_players=3,
            playtime_minutes=90,
            difficulty=Difficulty.MEDIUM,
        )
        self.alice = Player.objects.create(nickname="alice", email="alice@example.com")
        self.bob = Player.objects.create(nickname="bob", email="bob@example.com")
        self.carol = Player.objects.create(nickname="carol", email="carol@example.com")
        self.session = Session.objects.create(game=self.game, table_number=4, started_at=STARTED_AT)
        self.session.players.set([self.alice, self.bob])


class GameEndpointTests(CafeApiTestCase):
    def test_crud_round_trip(self) -> None:
        payload = {
            "title": "Azul",
            "min_players": 2,
            "max_players": 4,
            "playtime_minutes": 45,
            "difficulty": "easy",
        }
        created = self.client.post("/api/games/", payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        game_url = f"/api/games/{created.data['id']}/"

        self.assertEqual(self.client.get("/api/games/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(game_url).data["title"], "Azul")

        replaced = self.client.put(game_url, {**payload, "title": "Azul 2"}, format="json")
        self.assertEqual(replaced.data["title"], "Azul 2")
        patched = self.client.patch(game_url, {"difficulty": "hard"}, format="json")
        self.assertEqual(patched.data["difficulty"], "hard")

        self.assertEqual(self.client.delete(game_url).status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.get(game_url).status_code, status.HTTP_404_NOT_FOUND)

    def test_min_players_above_max_is_rejected(self) -> None:
        response = self.client.patch(
            f"/api/games/{self.game.pk}/", {"min_players": 5}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("max_players", response.data)

    def test_unknown_difficulty_is_rejected(self) -> None:
        response = self.client.patch(
            f"/api/games/{self.game.pk}/", {"difficulty": "brutal"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deleting_game_with_sessions_conflicts(self) -> None:
        response = self.client.delete(f"/api/games/{self.game.pk}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_game_sessions(self) -> None:
        response = self.client.get(f"/api/games/{self.game.pk}/sessions/")
        self.assertEqual([session["id"] for session in response.data], [self.session.pk])


class PlayerEndpointTests(CafeApiTestCase):
    def test_duplicate_nickname_is_rejected(self) -> None:
        response = self.client.post(
            "/api/players/", {"nickname": "alice", "email": "new@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_email_is_rejected(self) -> None:
        response = self.client.post(
            "/api/players/", {"nickname": "dave", "email": "not-an-email"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_player_sessions(self) -> None:
        response = self.client.get(f"/api/players/{self.alice.pk}/sessions/")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.client.get(f"/api/players/{self.carol.pk}/sessions/").data, [])


class SessionEndpointTests(CafeApiTestCase):
    def test_create_session(self) -> None:
        payload = {
            "game": self.game.pk,
            "table_number": 7,
            "started_at": STARTED_AT,
            "players": [self.alice.pk, self.carol.pk],
        }
        response = self.client.post("/api/sessions/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["game_title"], "Catan")

    def test_too_few_players_is_rejected(self) -> None:
        payload = {"game": self.game.pk, "table_number": 7, "started_at": STARTED_AT, "players": []}
        response = self.client.post("/api/sessions/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("players", response.data)

    def test_unknown_game_is_rejected(self) -> None:
        payload = {
            "game": 999,
            "table_number": 7,
            "started_at": STARTED_AT,
            "players": [self.alice.pk, self.bob.pk],
        }
        response = self.client.post("/api/sessions/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_notes_keeps_roster(self) -> None:
        response = self.client.patch(
            f"/api/sessions/{self.session.pk}/", {"notes": "Close game"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["players"]), 2)

    def test_session_players_add_and_remove(self) -> None:
        players_url = f"/api/sessions/{self.session.pk}/players/"
        self.assertEqual(len(self.client.get(players_url).data), 2)

        added = self.client.post(players_url, {"player_id": self.carol.pk}, format="json")
        self.assertEqual(added.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(added.data["players"]), 3)

        removed = self.client.delete(f"{players_url}{self.carol.pk}/")
        self.assertEqual(removed.status_code, status.HTTP_204_NO_CONTENT)
        missing = self.client.delete(f"{players_url}{self.carol.pk}/")
        self.assertEqual(missing.status_code, status.HTTP_404_NOT_FOUND)

    def test_adding_player_twice_is_rejected(self) -> None:
        response = self.client.post(
            f"/api/sessions/{self.session.pk}/players/", {"player_id": self.alice.pk}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adding_player_to_full_session_is_rejected(self) -> None:
        dave = Player.objects.create(nickname="dave", email="dave@example.com")
        self.session.players.add(self.carol)
        response = self.client.post(
            f"/api/sessions/{self.session.pk}/players/", {"player_id": dave.pk}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_session(self) -> None:
        response = self.client.delete(f"/api/sessions/{self.session.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
