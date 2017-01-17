from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.views.generic import TemplateView

from accounts.forms import LoginForm


def logout_view(request):
    logout(request)
    return redirect('main.main')


class LoginView(TemplateView):
    template_name = "accounts/login.html"

    def get_context_data(self, **kwargs):
        return {'form': LoginForm()}

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None and user.is_active:
                login(request, user)
                return redirect('/')
            else:
                form.add_error(None, "Authentication failed")
        return self.render_to_response({'form': form})
