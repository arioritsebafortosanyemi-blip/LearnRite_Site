from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from store.forms import SearchForm
from accounts.forms import AccountSetupForm, ProfileForm, RegisterForm


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("index")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {
        "register_form": form,
        "form": SearchForm(request.GET),
    })


@login_required
def confirm_account_setup(request):
    profile = request.user.profile
    if profile.profile_confirmed:
        return redirect("index")
    if request.method == "POST":
        setup_form = AccountSetupForm(request.POST, instance=profile)
        if setup_form.is_valid():
            setup_form.save()
            return redirect("index")
    else:
        setup_form = AccountSetupForm(instance=profile)
    return render(request, "accounts/confirm_account_setup.html", {
        "setup_form": setup_form,
        "form": SearchForm(request.GET),
    })


@login_required
def profile(request):
    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=request.user.profile)
        if profile_form.is_valid():
            profile_form.save()
            return redirect("profile")
    else:
        profile_form = ProfileForm(instance=request.user.profile)
    return render(request, "accounts/profile.html", {
        "profile_form": profile_form,
        "form": SearchForm(request.GET),
    })
