from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.StaffLoginView.as_view(), name="login"),
    path("logout/", views.StaffLogoutView.as_view(), name="logout"),
    path("password/", views.StaffPasswordChangeView.as_view(), name="password_change"),
    path("profile/", views.profile, name="profile"),
]
