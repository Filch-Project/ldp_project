from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .models import Profile
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, DraftOptionsForm, LeagueSettingsForm
from django.contrib.auth.decorators import login_required

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Your account has been created!  You are now logged in.')
            #logged the user in
            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'],
                                    )
            login(request, new_user)
            return redirect('profile')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your Profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
    }
    return render(request, 'users/profile.html', context)

@login_required
def leaguesettings(request):
    if request.method == 'POST':
        s_form = LeagueSettingsForm(request.POST, request.FILES, instance=request.user.profile)
        if s_form.is_valid():
            s_form.save()
            messages.success(request, f'Your League Settings have been updated!')
            return redirect('leaguesettings')
    else:
        s_form = LeagueSettingsForm(instance=request.user.profile)

    context = {
        's_form': s_form,
    }
    return render(request, 'users/leaguesettings.html', context)

@login_required
def draftoptions(request):
    if request.method == 'POST':
        d_form = DraftOptionsForm(request.POST, request.FILES, instance=request.user.profile)
        if d_form.is_valid():

            num_players_list = Profile.objects.values_list('numberofplayersperteam',flat=True).filter(user = request.user)  #numberofteamsinleague
            num_players = int(num_players_list[0])
            formvalues = [int(d_form['qb'].value()), int(d_form['rb'].value()), int(d_form['wr'].value()), int(d_form['te'].value()), int(d_form['d'].value()), int(d_form['k'].value())]
            formsum = sum(formvalues)
            if formsum != num_players:
                messages.warning(request, f'The total does not match the number of of draftable players.  Your values were not saved.')
                return redirect('draftoptions')
            else:
                d_form.save()
                messages.success(request, f'Your Draft Options have been updated!')
                return redirect('draftoptions')
    else:
        d_form = DraftOptionsForm(instance=request.user.profile)

    context = {
        'd_form': d_form,
    }
    return render(request, 'users/draftoptions.html', context)
