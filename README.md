# HW3 — Board Game Café REST API

A REST API for a board game café. It tracks the café's games, the players who visit, and the sessions where players sit down to play.

Built with Django 5 and Django REST Framework on SQLite, through the Django ORM. There are three models: `Game`, `Player` and `Session`. A game has many sessions (one-to-many), and sessions and players are many-to-many. The 23 endpoints cover GET, POST, PUT, PATCH and DELETE, plus nested routes such as `/games/{id}/sessions/`.

Every endpoint is documented in [`docs/API.md`](docs/API.md). The Postman collection is [`postman/board_game_cafe.postman_collection.json`](postman/board_game_cafe.postman_collection.json).

## Run

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The API is served at `http://127.0.0.1:8000/api/`. That URL also opens DRF's browsable API.

## Test

```bash
python manage.py test cafe
```

Postman: import the collection, then use **Run collection** to run the folders top to bottom. Each request saves the ids it creates into collection variables. The last folder deletes everything it created, so you can run the collection again.

From the command line:

```bash
npx newman run postman/board_game_cafe.postman_collection.json
```
