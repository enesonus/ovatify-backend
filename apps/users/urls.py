from django.urls import path

from apps.users import views

urlpatterns = [
    path('get-all/', view=views.get_all_users, name='get-all-users'),
    path('return-post-body/', view=views.return_post_body, name='return-post-body'),
    path('user-preferences/',view = views.user_preferences_create, name='user_preferences_create')
]
