from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from scipy.optimize import curve_fit
from io import StringIO
from .forms import SignupForm, LoginForm
from .models import Otp
from .module import fourpl

import folium, geocoder
import pandas as pd

map_markers = []

def test(request):
    template_name = "natrosensor/test.html"
    return render(request, template_name, context={"template_name": "Test"})

def index(request):
    map = folium.Map([14.1608, 121.2453], zoom_start=18)
    folium.Marker([14.1608, 121.2453], popup="", icon=folium.Icon(color='blue', icon='crosshairs', prefix='fa')).add_to(map)
    map_embed = map._repr_html_()

    template_name = "natrosensor/index.html"
    return render(request, template_name, context={"template_name": "Index", "map": map_embed})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)    
                return redirect('/dashboard')
    else:
        form = LoginForm()

    template_name = "natrosensor/login.html"
    return render(request, template_name, context={"template_name": "Login", 'form': form})

def user_logout(request):
    global map_markers
    map_markers = []

    logout(request)
    return redirect('/login')

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():   
            user = form.save(commit=False)  
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']

            if not password2:
                raise form.ValidationError("You must confirm your password")
            if password1 != password2:
                raise form.ValidationError("Your passwords do not match")
            else:
                user.set_password(password2)
                user.save()
                return redirect('/login')
    else:
        form = SignupForm()

    template_name = "natrosensor/signup.html"
    return render(request, template_name, context={"template_name": "Signup", 'form': form})

def verify(request, email):
    user = get_user_model().objects.get(email=email)
    otp = Otp.objects.filter(user=user).last()

    if request.method == "POST":
        if otp.code == request.POST.get('code'):
            user.is_active = True
            user.save()
            return redirect('/login')

@login_required(login_url='/login')
def location(request):
    global map_markers

    # g = geocoder.ip('me')
    g = geocoder.google([45.15, -75.14], method='reverse')
    g.latlng = (14.1769, 121.2225)
    g.city = "Los Baños"
    g.country = "PH"
    g.postal = "4030"
    map = folium.Map(location=g.latlng, zoom_start=5)
    folium.Marker(g.latlng, popup=g.address,icon=folium.Icon(color='blue', icon='crosshairs', prefix='fa')).add_to(map)

    if request.method == 'POST':
        lat = float(request.POST.get('loc_lat'))
        lng = float(request.POST.get('loc_lng'))        
        g = geocoder.google([lat, lng], method='reverse')
        g.latlng = [lat, lng]

        map_markers.append({
            'lat': lat,
            'lng': lng,
            'addr': g
        })     

    for marker in map_markers:
        folium.Marker([marker['lat'], marker['lng']], popup="[" + str(marker['lat']) + "," + str(marker['lng']) + "]" + str(marker['addr']), icon=folium.Icon(color='blue', icon='crosshairs', prefix='fa')).add_to(map)

    template_name = "natrosensor/location.html"
    map.add_child(folium.LatLngPopup())
    map_embed = map._repr_html_()
    return render(request, template_name, context={"template_name": "Location", "map": map_embed, "location": g})

@login_required(login_url='/login')
def dashboard(request):
    # user = {}
    # user['first_name'] = request.user.first_name if request.user.is_authenticated else None
    # user['last_name'] = request.user.last_name if request.user.is_authenticated else None

    template_name = "natrosensor/dashboard.html"
    return render(request, template_name, context={"template_name": "Dashboard"})

@login_required(login_url='/login')
def process(request):
    template_name = "natrosensor/process.html"
    return render(request, template_name, context={"template_name": "Process"})

@login_required(login_url='/login')
def records(request):
    template_name = "natrosensor/records.html"
    return render(request, template_name, context={"template_name": "Records"})

@login_required(login_url='/login')
def about(request):
    template_name = "natrosensor/about.html"
    return render(request, template_name, context={"template_name": "About"})

@login_required(login_url='/login')
def profile(request):
    user = {}
    user['first_name'] = request.user.first_name if request.user.is_authenticated else None
    user['last_name'] = request.user.last_name if request.user.is_authenticated else None
    user['institution'] = request.user.institution if request.user.is_authenticated else None

    template_name = "natrosensor/profile.html"
    return render(request, template_name, context={"template_name": "Profile", "user": user})

@login_required(login_url='/login')
def settings(request):
    template_name = "natrosensor/settings.html"
    return render(request, template_name, context={"template_name": "Settings"})

@login_required(login_url='/login')
def result(request):
    process_name = request.POST.get('process_name') 
    process_med = request.POST.get('process_med', 'Penicillin')
    process_trial = int(request.POST.get('process_trial'))
    process_file = request.FILES['process_file']
    process_note = request.POST.get('process_note')
    process_temp = request.POST.get('process_temp')
    process_ph = request.POST.get('process_ph')

    process = {
        'name': process_name,
        'med': process_med,
        'trial': process_trial,
        'note': process_note,
        'temp': process_temp,
        'pH': process_ph,
    }

    df = pd.read_csv(process_file)
    size = fourpl.graph_settings()
    fig, y_int, slope = fourpl.fourpl(df, size)

    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    graph = imgdata.getvalue()    

    template_name = "natrosensor/result.html"
    return render(request, template_name, context={"template_name": "Result", "graph": graph, "y_int": y_int, "slope": slope, "process": process})