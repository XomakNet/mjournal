from django.conf.urls import url

from accounts.views import LoginView, logout_view


urlpatterns = [
    url(r'^login/$', LoginView.as_view()),
    url(r'^logout/$', logout_view, name='accounts.logout')
]