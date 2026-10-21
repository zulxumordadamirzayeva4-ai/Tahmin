from django.urls import path
from games.views import (
    login_view,
    register_view,
    logout_view,
    index_view,
    guess_api,
    reset_api,
    leaderboard_api,
)

urlpatterns = [
    path('', index_view, name='index'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('api/guess/', guess_api, name='api_guess'),
    path('api/reset/', reset_api, name='api_reset'),
    path('api/leaderboard/', leaderboard_api, name='api_leaderboard'),
]

