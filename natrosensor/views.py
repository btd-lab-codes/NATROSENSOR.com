from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from scipy.optimize import curve_fit
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from io import StringIO
from datetime import datetime, timedelta
from .forms import SignupForm, LoginForm
from .models import Otp, Event, Records, User
from .module import fourpl

import matplotlib.pyplot as plt
import folium, branca, geocoder, base64, io, os
import pandas as pd

LOC_INFO = {
    'region': pd.read_csv(os.path.join(os.path.dirname(__file__), "module/csv/table_region.csv")).to_dict('split')['data'],
    'province': pd.read_csv(os.path.join(os.path.dirname(__file__), "module/csv/table_province.csv")).to_dict('split')['data'],
    'municipality': pd.read_csv(os.path.join(os.path.dirname(__file__), "module/csv/table_municipality.csv")).to_dict('split')['data'],
    'barangay': pd.read_csv(os.path.join(os.path.dirname(__file__), "module/csv/table_barangay.csv")).to_dict('split')['data']
}

map_markers = []

@login_required(login_url='/login')
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

def signup(request, success=False):
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
                success = True
    else:
        form = SignupForm()

    template_name = "natrosensor/signup.html"
    return render(request, template_name, context={"template_name": "Signup", 'form': form, 'success': success})

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

    g = geocoder.google([45.15, -75.14], method='reverse')
    g.latlng = (14.1769, 121.2225)
    g.city = "Los Baños"
    g.country = "PH"
    g.postal = "4030"

    map = folium.Map(location=g.latlng, zoom_start=5)
    folium.Marker(g.latlng, popup=g.address,icon=folium.Icon(color='blue', icon='crosshairs', prefix='fa')).add_to(map)

    current_location = geocoder.ip("me")
    g_curr = geocoder.osm(current_location.latlng, method='reverse')
    print(g_curr.address) 
    print(g_curr) 

    for marker in map_markers:
        folium.Marker([marker['lat'], marker['lng']], popup="[" + str(marker['lat']) + "," + str(marker['lng']) + "]" + str(marker['addr']), icon=folium.Icon(color='blue', icon='crosshairs', prefix='fa')).add_to(map)

    template_name = "natrosensor/location.html"
    map.add_child(folium.LatLngPopup())

    fig = branca.element.Figure(height='100%')
    fig.add_child(map)
    map_embed = fig._repr_html_()
    return render(request, template_name, context={"template_name": "Location", "map": map_embed, "location": g})

@login_required(login_url='/login')
def dashboard(request):
    first_name = request.user.first_name if request.user.is_authenticated else "User"
    process = Records.objects.filter(user=request.user)
    events = Event.objects.filter(user=request.user)
    user_count = User.objects.all().count()    
    process_count = {}

    today = datetime.today()
    for index in range(7, 0, -1):
        start = today - timedelta(days=index-1)
        proc = Records.objects.filter(user=request.user).filter(created_at__date=start)
        process_count[timezone.localdate(timezone.make_aware(start)).strftime("%B %d, %Y")] = proc.count()

    label = list(process_count.keys())
    value = list(process_count.values())

    fig = plt.figure()
    plt.plot(label, value, marker='o')
    plt.xlabel("Date (Last 7 Days)")
    plt.ylabel("Process Count")

    fig = FigureCanvas(fig)
    imgdata = io.BytesIO()
    fig.print_png(imgdata)
    imgdata.seek(0)
    graph = "data:image/png;base64," + base64.b64encode(imgdata.getvalue()).decode('utf-8')
    
    template_name = "natrosensor/dashboard.html"
    return render(request, template_name, context={"template_name": "Dashboard", "first_name": first_name, "user_count": user_count, "process": process, "events": events, "graph": graph})

@login_required(login_url='/login')
def process(request):
    if request.method == "POST":
        process_file = request.FILES['process_file']   

        process = {
            'name': request.POST.get('process_name'),
            'antibiotics': request.POST.get('process_med'),
            'trial': int(request.POST.get('process_trial')),
            'region': request.POST.get('process_region'),
            'province': request.POST.get('process_province'),
            'municipality': request.POST.get('process_municipality'),
            'barangay': request.POST.get('process_barangay'),
            'address': request.POST.get('process_addr'),
            'temperature': request.POST.get('process_temp'),
            'ph': request.POST.get('process_ph'),
            'note': request.POST.get('process_note')
        }

        df = pd.read_csv(process_file)
        size = fourpl.graph_settings()
        fig, y_int, slope = fourpl.fourpl(df, size)

        imgdata = io.BytesIO()
        fig.print_png(imgdata)
        imgdata.seek(0)
        graph = base64.b64encode(imgdata.getvalue()).decode('utf-8')

        request.session['process'] = process
        request.session['graph'] = "data:image/png;base64," + graph
        request.session['y_int'] = y_int
        request.session['slope'] = slope

        request.session.modified = True
        return redirect('/result')

    template_name = "natrosensor/process.html"
    return render(request, template_name, context={"template_name": "Process", "loc_info": LOC_INFO})

@login_required(login_url='/login')
def autolocate(request):
    pass

@login_required(login_url='/login')
def records(request):
    records = Records.objects.filter(user=request.user)
    headers = ["Name", "Date", "Time", "Antibiotics", "Details"]

    template_name = "natrosensor/records.html"
    return render(request, template_name, context={"template_name": "Records", "records": records, "headers": headers})

@login_required(login_url='/login')
def schedule(request):
    if request.method == "POST":
        name = request.POST.get('event_name')
        date = request.POST.get('event_date')
        time = request.POST.get('event_time')
        detail = request.POST.get('event_detail')
        
        new_event = Event(name=name, date=date, time=time, detail=detail, user=request.user)
        new_event.save()

    events = Event.objects.filter(user=request.user)
    template_name = "natrosensor/schedule.html"
    return render(request, template_name, context={"template_name": "Schedule", "events": events})

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
    process = request.session.get('process')
    graph = request.session.get('graph')
    y_int = request.session.get('y_int')
    slope = request.session.get('slope') 

    if request.method == "POST":
        new_result = Records(
            name=process['name'], 
            antibiotics=process['antibiotics'], 
            trial=process['trial'], 
            region=process['region'],
            province=process['province'],
            municipality=process['municipality'],
            barangay=process['barangay'],
            address=process['address'],
            temperature=process['temperature'], 
            ph=process['ph'], 
            note=process['note'], 
            graph=graph, 
            user=request.user
        )
        new_result.save()

    template_name = "natrosensor/result.html"
    return render(request, template_name, context={"template_name": "Result", "graph": graph, "y_int": y_int, "slope": slope, "process": process})
