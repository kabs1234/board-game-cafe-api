# Board Game Café API — Endpoint Reference

Base URL: `http://127.0.0.1:8000/api`  
All bodies are JSON (`Content-Type: application/json`). No authentication.

## Endpoints (23)

| # | Method | URL |
|---|--------|-----|
| 1 | GET | `/games/` |
| 2 | POST | `/games/` |
| 3 | GET | `/games/{id}/` |
| 4 | PUT | `/games/{id}/` |
| 5 | PATCH | `/games/{id}/` |
| 6 | DELETE | `/games/{id}/` |
| 7 | GET | `/games/{id}/sessions/` |
| 8 | GET | `/players/` |
| 9 | POST | `/players/` |
| 10 | GET | `/players/{id}/` |
| 11 | PUT | `/players/{id}/` |
| 12 | PATCH | `/players/{id}/` |
| 13 | DELETE | `/players/{id}/` |
| 14 | GET | `/players/{id}/sessions/` |
| 15 | GET | `/sessions/` |
| 16 | POST | `/sessions/` |
| 17 | GET | `/sessions/{id}/` |
| 18 | PUT | `/sessions/{id}/` |
| 19 | PATCH | `/sessions/{id}/` |
| 20 | DELETE | `/sessions/{id}/` |
| 21 | GET | `/sessions/{id}/players/` |
| 22 | POST | `/sessions/{id}/players/` |
| 23 | DELETE | `/sessions/{id}/players/{player_id}/` |

## Data model

```
Game 1 ──── * Session * ──── * Player
```

| Model | Fields |
|-------|--------|
| **Game** | `id`, `title` (unique, ≤120), `min_players` (1–20), `max_players` (1–20, ≥ min), `playtime_minutes` (≥1), `difficulty` (`easy` \| `medium` \| `hard`), `created_at` (read-only) |
| **Player** | `id`, `nickname` (unique, ≤40), `email` (unique, valid email), `joined_at` (read-only) |
| **Session** | `id`, `game` (Game id), `game_title` (read-only), `table_number` (1–50), `started_at` (ISO 8601 datetime), `players` (list of Player ids), `notes` (optional) |

Relationships:
- **Game → Session**: one-to-many (`Session.game` foreign key, `on_delete=PROTECT`).
- **Session ↔ Player**: many-to-many (`Session.players`).

## Status codes

| Code | When |
|------|------|
| `200 OK` | Successful GET / PUT / PATCH |
| `201 Created` | Successful POST |
| `204 No Content` | Successful DELETE |
| `400 Bad Request` | Validation failed. The body maps each field to its error messages, e.g. `{"max_players": ["max_players must be greater than or equal to min_players."]}` |
| `404 Not Found` | The id does not exist: `{"detail": "Not found."}` |
| `405 Method Not Allowed` | Method not supported on that URL |
| `409 Conflict` | Deleting a game that still has sessions: `{"detail": "Cannot delete: other records still reference this object."}` |

---

## Games

### `GET /games/`
List all games (sorted by title).  
**Response 200**
```json
[
  {"id": 1, "title": "Catan", "min_players": 2, "max_players": 3,
   "playtime_minutes": 90, "difficulty": "medium", "created_at": "2026-11-14T10:00:00Z"}
]
```

### `POST /games/`
Create a game.  
**Body**
```json
{"title": "Catan", "min_players": 2, "max_players": 3, "playtime_minutes": 90, "difficulty": "medium"}
```
**Response 201**: the created game.  
**400**: missing or invalid field, duplicate `title`, `min_players > max_players`, unknown `difficulty`.

### `GET /games/{id}/`
Get one game. **200** returns the game. **404** if the id is unknown.

### `PUT /games/{id}/`
Replace a game. The body needs every writable field (same as POST). **200**, **400**, **404**.

### `PATCH /games/{id}/`
Partially update a game, e.g. `{"difficulty": "hard"}`. **200**, **400**, **404**.

### `DELETE /games/{id}/`
Delete a game. **204**, **404**, and **409** if the game still has sessions.

### `GET /games/{id}/sessions/`
All sessions played with this game (related data). **200** returns a list of sessions. **404** if the game is unknown.

---

## Players

### `GET /players/`
List all players (sorted by nickname).  
**Response 200**
```json
[{"id": 1, "nickname": "alice", "email": "alice@example.com", "joined_at": "2026-11-14T10:00:00Z"}]
```

### `POST /players/`
**Body**: `{"nickname": "alice", "email": "alice@example.com"}`  
**201** returns the created player. **400** for a duplicate nickname or email, or an invalid email.

### `GET /players/{id}/`
**200** returns the player. **404** if the id is unknown.

### `PUT /players/{id}/`
**Body**: `{"nickname": "...", "email": "..."}`. **200**, **400**, **404**.

### `PATCH /players/{id}/`
**Body**: any subset, e.g. `{"email": "new@example.com"}`. **200**, **400**, **404**.

### `DELETE /players/{id}/`
**204**, **404**. The player is also removed from every session they were in.

### `GET /players/{id}/sessions/`
All sessions this player joined (related data). **200** returns a list of sessions. **404** if the player is unknown.

---

## Sessions

### `GET /sessions/`
List sessions, newest first.  
**Response 200**
```json
[
  {"id": 1, "game": 1, "game_title": "Catan", "table_number": 4,
   "started_at": "2026-11-14T18:00:00Z", "players": [1, 2], "notes": "Friday night"}
]
```

### `POST /sessions/`
**Body**
```json
{"game": 1, "table_number": 4, "started_at": "2026-11-14T18:00:00Z", "players": [1, 2], "notes": "Friday night"}
```
**201** returns the created session.  
**400** when:
- `game` or a player id does not exist
- a player is listed twice
- the number of players is outside the game's `min_players`–`max_players` range
- `table_number` is outside 1–50

### `GET /sessions/{id}/`
**200** returns the session. **404** if the id is unknown.

### `PUT /sessions/{id}/`
Replace the session. The body has the same fields as POST and the same player-count rule applies. **200**, **400**, **404**.

### `PATCH /sessions/{id}/`
Partial update, e.g. `{"notes": "Alice won"}`. The player-count rule is re-checked only when `game` or `players` changes. **200**, **400**, **404**.

### `DELETE /sessions/{id}/`
**204**, **404**.

### `GET /sessions/{id}/players/`
Players seated at this session (related data). **200** returns a list of players. **404** if the session is unknown.

### `POST /sessions/{id}/players/`
Seat one more player.  
**Body**: `{"player_id": 3}`  
**201** returns the updated session.  
**400** when the player does not exist, is already in the session, or the session is full (the game's `max_players` is reached).  
**404** if the session is unknown.

### `DELETE /sessions/{id}/players/{player_id}/`
A player leaves the session. **204**. **404** if the session is unknown or the player is not in it.
