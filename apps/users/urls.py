from django.urls import path

from apps.users import views

urlpatterns = [
    path('get-all/', view=views.get_all_users, name='get-all-users'),
    path('return-post-body/', view=views.return_post_body, name='return-post-body'),
    path('create-user/', view=views.create_user, name='create-user'),
    path('login/', view=views.login, name='login'),
    path('delete-user/', view=views.delete_user, name='delete-user'),
    path('update-user/', view=views.update_user, name='update-user'),
    path('remove-friend', view=views.remove_friend, name = 'remove-friend')
]
