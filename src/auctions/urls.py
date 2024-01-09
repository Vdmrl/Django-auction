from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create, name="creation"),
    path("categories", views.categories, name="categories"),
    path("categories/<str:category_name>", views.category, name="category"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("<int:index>", views.listing, name="listing"),
    path("<int:index>/add_to_watchlist", views.add_to_watchlist, name="add_to_watchlist"),
    path("<int:index>/close_listing", views.close_listing, name="close_listing"),
    path("<int:index>/like/<int:comment_index>", views.like, name="like"),
    path("<int:index>/dislike/<int:comment_index>", views.dislike, name="dislike"),
]
