from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Avg
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from datetime import datetime, timedelta
from .forms import SignupForm, LoginForm
from .models import Otp, Event, Records, User
from .module import fourpl

import matplotlib.pyplot as plt
import folium, branca, geocoder, base64, io, os
import pandas as pd
import osmnx as ox
import pyfirmata2, time

LOC_INFO = {
    'region': pd.read_csv(os.path.join(os.path.dirname(__file__), "module/csv/table_region.csv")).to_dict('split')['data'],
    'province': pd.read_csv(os.path.join(os.path.dirname(__file__), "module/csv/table_province.csv")).to_dict('split')['data'],
    'municipality': pd.read_csv(os.path.join(os.path.dirname(__file__), "module/csv/table_municipality.csv")).to_dict('split')['data'],
    'barangay': pd.read_csv(os.path.join(os.path.dirname(__file__), "module/csv/table_barangay.csv")).to_dict('split')['data']
}

@login_required(login_url='/login')
def test(request):
    # port = pyfirmata2.Arduino.AUTODETECT  # Automatically detect the port if unsure
    # # Initialize the board
    # board = pyfirmata2.Arduino(port)
    # # Blink an LED on a digital pin (e.g., D4)
    # pin = board.get_pin('d:4:o')  # 'd' for digital, '4' for GPIO4 (D4), 'o' for output

    # # Blink the LED in a loop
    # while True:
    #     pin.write(1)  # Turn on
    #     time.sleep(1)
    #     pin.write(0)  # Turn off
    #     time.sleep(1)

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
        
def center_geojson(name):
    name = name + ", Philippines"
    gdf = ox.geocode_to_gdf(name)
    geojson = gdf.__geo_interface__
    center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
    return geojson, center

def map_geojson(map, records, geojson, center, name, antibiotics):
    concentration = records.aggregate(Avg('concentration'))['concentration__avg']
    absorbance = records.aggregate(Avg('absorbance'))['absorbance__avg']
    popup = f'''
    <div style="width: 250px; text-align: center; gap: 10px;">
        <h6 style="font-size: 16px;"><strong>Data for {name} { "(" + antibiotics + ")" if antibiotics != "All" else ""}</strong></h6>
        <div style="display: flex; flex-wrap: wrap; font-size: 12px;">
            <div style="flex: 1 1 0; text-align: center;">
                <p style="margin: 0;"><strong>Total Count</strong></p>
            </div>
            <div style="flex: 1 1 0; text-align: center;">
                <p style="margin: 0;"><strong>Concentration (avg)</strong></p>
            </div>
            <div style="flex: 1 1 0; text-align: center;">
                <p style="margin: 0;"><strong>Absorbance (avg)</strong></p>
            </div>
        </div>
        <div style="display: flex; flex-wrap: wrap; font-size: 14px; margin-top: 10px;">
            <div style="flex: 1 1 0; text-align: center;">
                <p style="margin: 0;"><strong>{records.count()}</strong></p>
            </div>
            <div style="flex: 1 1 0; text-align: center;">
                <p style="margin: 0;"><strong>{round(concentration, 4)}</strong></p>
            </div>
            <div style="flex: 1 1 0; text-align: center;">
                <p style="margin: 0;"><strong>{round(absorbance, 4)}</strong></p>
            </div>
        </div>
    </div>
    '''

    folium.GeoJson(
        geojson,
        style_function=lambda feature: {
            'fillColor': 'red',
            'color': 'red',
            'weight': 1,
            'fillOpacity': absorbance
        }
    ).add_to(map)

    folium.Marker(
        location=center, 
        popup=folium.Popup(popup, max_width=300),
        icon=folium.Icon(icon='info-sign', color='blue')
    ).add_to(map)

@login_required(login_url='/login')
def location(request, antibiotics="All", division="Region"):
    if request.method == "POST":
        division = request.POST.get('location_division')
        antibiotics = request.POST.get('location_antibiotics')

    _, default_center = center_geojson("NCR")
    map = folium.Map(location=default_center, zoom_start=7)
    records = Records.objects.filter(user=request.user)

    if division == "Region":
        for name in list(set(records.values_list('region', flat=True).distinct())):
            region_geojson, region_center = center_geojson(name)
            records_region = records.filter(region=name)
            records_region = records_region.filter(antibiotics=antibiotics) if antibiotics != "All" else records_region
            map_geojson(map, records_region, region_geojson, region_center, name, antibiotics)
    elif division == "Province":
        for name in list(set(records.values_list('province', flat=True).distinct())):
            province_geojson, province_center = center_geojson(name)
            records_province = records.filter(province=name)
            records_province = records_province.filter(antibiotics=antibiotics) if antibiotics != "All" else records_province
            map_geojson(map, records_province, province_geojson, province_center, name, antibiotics)
    elif division == "Municipality":
        for municipality, province in list(set(records.values_list('municipality', 'province').distinct())):
            municipality_geojson, municipality_center = center_geojson(municipality + ", " + province)
            records_municipality = records.filter(municipality=municipality, province=province)
            records_municipality = records_municipality.filter(antibiotics=antibiotics) if antibiotics != "All" else records_municipality
            map_geojson(map, records_municipality, municipality_geojson, municipality_center, municipality + ", " + province, antibiotics)

    template_name = "natrosensor/location.html"
    map.add_child(folium.LatLngPopup())

    fig = branca.element.Figure(height='100%')
    fig.add_child(map)
    map_embed = fig._repr_html_()
    return render(request, template_name, context={"template_name": "Location", "map": map_embed, "loc_info": LOC_INFO, "antibiotics": antibiotics, "division": division})

@login_required(login_url='/login')
def dashboard(request):
    first_name = request.user.first_name if request.user.is_authenticated else "User"
    process = Records.objects.filter(user=request.user)
    events = Event.objects.filter(user=request.user).filter(date__gte=timezone.now().date())
    user_count = User.objects.all().count()    
    process_count = {}

    today = datetime.today()
    for index in range(7, 0, -1):
        start = today - timedelta(days=index-1)
        proc = Records.objects.filter(user=request.user).filter(created_at__date=start)
        process_count[timezone.localdate(timezone.make_aware(start)).strftime("%m/%d/%Y")] = proc.count()

    label = list(process_count.keys())
    value = list(process_count.values())

    fig = plt.figure()
    plt.plot(label, value, marker='o')
    plt.xlabel("Date (Last 7 Days)")
    plt.ylabel("Process Count")
    plt.xticks(rotation=10)
    plt.tight_layout()

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
        fig, y_int, slope, c50, c50_y = fourpl.fourpl(df, size)

        imgdata = io.BytesIO()
        fig.print_png(imgdata)
        imgdata.seek(0)
        graph = base64.b64encode(imgdata.getvalue()).decode('utf-8')

        request.session['process'] = process
        request.session['graph'] = "data:image/png;base64," + graph
        request.session['y_int'] = y_int
        request.session['slope'] = slope
        request.session['c50'] = c50
        request.session['c50_y'] = c50_y

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
    c50 = request.session.get('c50')
    c50_y = request.session.get('c50_y')

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
            concentration=c50,
            absorbance=c50_y,
            user=request.user
        )
        new_result.save()

    template_name = "natrosensor/result.html"
    return render(request, template_name, context={"template_name": "Result", "graph": graph, "y_int": y_int, "slope": slope, "c50": c50, "c50_y": c50_y, "process": process})
