from django.urls import path

from users.views import registration_view, index, logout_view, login_view, account_view, must_authenticate_view, edit_account, account_search_view

app_name = 'users'
urlpatterns = [
    path('', index, name='index'),
    path('<int:user_id>/edit/', edit_account, name='profile'),
    #path('profile/<int:pk>/', follow, name='follow'),
    path('login/', login_view, name='login'),
    path('must_authenticate/', must_authenticate_view, name='must_authenticate'),
    path('register/', registration_view, name='registration_view'),
    path('logout/', logout_view, name='logout'),
    path('search/', account_search_view, name='search'),
    path('<str:username>/', account_view, name='profile_view'),

]