from rest_framework.routers import DefaultRouter

from .views import GameViewSet, PlayerViewSet, SessionViewSet

router = DefaultRouter()
router.register("games", GameViewSet)
router.register("players", PlayerViewSet)
router.register("sessions", SessionViewSet)

urlpatterns = router.urls
