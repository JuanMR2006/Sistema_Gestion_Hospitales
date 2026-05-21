from django.urls import path

from .views import (
    CustomLoginView,
    CustomLogoutView,
    RegisterView,
    UserListView,
    UserToggleActiveView,
    UserUpdateView,
)

app_name = 'users'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('', UserListView.as_view(), name='user_list'),
    path('<int:pk>/edit/', UserUpdateView.as_view(), name='user_update'),
    path('<int:pk>/toggle/', UserToggleActiveView.as_view(), name='user_toggle'),
]
