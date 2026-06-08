from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Avg
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse

from .forms import SignupForm, LoginForm
from .models import Otp, Event, Records, User
from .module import fourpl
from .constants import *
from .utils.send_otp import send_otp

from datetime import datetime, timedelta
from calendar import monthrange

import matplotlib.pyplot as plt
import pandas as pd
import osmnx as ox
import pyfirmata2, time
import folium, branca, geocoder, base64, io, os, re, json

# For Testing Purposes on the Page
@login_required(login_url='/login')
def test(request):
    events = Event.objects.filter(user=request.user)
    template_name = "natrosensor/schedule/page.html"
    return render(request, template_name, context={"template_name": "Schedule", "events": events})

# Landing Page Function
def welcome(request):
    # Initialize Map for the Location of CEAT
    map = folium.Map([14.1608, 121.2453], zoom_start=18)
    folium.Marker([14.1608, 121.2453], popup="", icon=folium.Icon(color='blue', icon='crosshairs', prefix='fa')).add_to(map)

    template_name = "natrosensor/welcome/page.html" if request.headers.get('HX-Request') else "natrosensor/welcome/loading.html"    
    context = {"template_name": "Landing", "project_leader": PROJECT_LEADER, "project_staff": PROJECT_STAFF, "map": map._repr_html_()}

    # To ensure that the loading screen will work
    if request.headers.get('HX-Request'): 
        time.sleep(1)

    return render(request, template_name, context)

# Login Page Function
def user_login(request, error=False):
    # When the user login the account
    if request.method == 'POST':
        form = LoginForm(request.POST)

        # Check if the email and password are not empty
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Check if the password matched from the account email
            user = authenticate(request, email=email, password=password)

            # If the login credentials is correct
            if user:
                login(request, user)
                response = JsonResponse({"success": True})

                # Set the route to the dashboard page
                response["HX-Redirect"] = "/dashboard"
                return response    
            else:
                error = True
    else:
        # Show the login form 
        form = LoginForm()

    template_name = "natrosensor/login/page.html"
    context = {"template_name": "Trial", "form": form, "error": error}
    return render(request, template_name, context)

# Logout Function
def user_logout(request):
    # For removing the credentials from the request
    logout(request)
    response = JsonResponse({"success": True})

    # Set the route to the login page
    response["HX-Redirect"] = "/login"
    return response   

# Signup Page Function
def signup(request):
    # When the user is finished signing up
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid(): 
            # Get the codes from each inputs and combine it into one
            otp_code = "".join([
                request.POST.get('otp_1'),
                request.POST.get('otp_2'),
                request.POST.get('otp_3'),
                request.POST.get('otp_4'),
                request.POST.get('otp_5'),
                request.POST.get('otp_6'),
            ])

            try:
                # Check if the OTP code is existed and valid from the assigned email
                otp_entry = Otp.objects.get(email=form.cleaned_data['email'])
            
            # Check if the assigned otp code exist
            except Otp.DoesNotExist:
                return JsonResponse({"success": False, "message": "Your OTP has expired. Please request a new one."})

            # Check if the otp code is already expired (beyond 5 minutes)
            if not otp_entry.is_valid():
                return JsonResponse({"success": False, "message": "Your OTP has expired. Please request a new one."})

            # Check if the input code matched to the otp code
            if not otp_entry.checkCode(otp_code):
                return JsonResponse({"success": False, "message": "Invalid OTP. Please try again."})
            
            user = form.save(commit=False)  
            password2 = form.cleaned_data['password2']

            # Set the assigned password to the user and save it for successful creation of the account
            user.set_password(password2)
            user.save()

            # Delete the otp code once the user is successfully created
            otp_entry.delete()
            return JsonResponse({"success": True, "message": ""})
    else:
        # Show the signup form
        form = SignupForm()

    template_name = "natrosensor/signup/page.html"
    return render(request, template_name, context={"template_name": "Signup", 'form': form})

# Checking Email Function
def check_email(request):
    email = request.GET.get('email').strip()

    # Check if the input email is empty
    if not email:
        return HttpResponse("<span> Please enter an email address </span>")
    
    # Check if the input email is aligned to the email format 
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):  
        return HttpResponse("<span> Invalid email format </span>")
    
    # Check if the input email have already the existing account
    if User.objects.filter(email=email).exists():
        return HttpResponse("<span> Email address is already taken </span>")
    
    # Return the success status when no error occured 
    return HttpResponse(status=204)
        
# Creating OTP code Function
def generate_code(request):
    email = request.GET.get('email').strip()
    
    # Get the OTP code from the assigned email
    otp_created, valid_until = send_otp(email)

    # Check if the OTP code has already existed and still valid
    message = "successfully" if otp_created else "already"

    # Return the message once the OTP code is created
    return JsonResponse({"valid_until": valid_until, "message": "Your OTP has been " + message + " sent!"})

# Function for determining the center of the bounded geojson on the specified location  
def center_geojson(name):
    name = name + ", Philippines"
    # Finding the specified location 
    gdf = ox.geocode_to_gdf(name) 
    # Finding the bounding geometry of the specified location 
    geojson = gdf.__geo_interface__
    # Finding the center of the bounded geojson
    center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
    return geojson, center

# Function for plotting the bounded geojson into the map
def map_geojson(map, records, geojson, center, name, antibiotics):
    # When the record details is not empty
    if records.count() != 0:
        # Assign the average concentration and absorbance from the sorted records based on the specified location
        concentration = records.aggregate(Avg('concentration'))['concentration__avg']
        absorbance = records.aggregate(Avg('absorbance'))['absorbance__avg']

        # For showing the details needed when clicking the marker from the centroid of the map
        popup = f'''
        <div style="width: 250px; text-align: center; gap: 10px;">
            <h6 style="font-size: 16px;"><strong>Data for {name} { "(" + antibiotics + ")" if antibiotics != "All" else ""}</strong></h6>
            <div style="display: flex; flex-wrap: wrap; font-size: 12px;">
                <div style="flex: 1 1 0; text-align: center;">
                    <p style="margin: 0;"><strong>Total Count</strong></p>
                </div>
                <div style="flex: 1 1 0; text-align: center;">
                    <p style="margin: 0;"><strong>DPV reading (avg)</strong></p>
                </div>
                <div style="flex: 1 1 0; text-align: center;">
                    <p style="margin: 0;"><strong>Dose, ppm (avg)</strong></p>
                </div>
            </div>
            <div style="display: flex; flex-wrap: wrap; font-size: 14px; margin-top: 10px;">
                <div style="flex: 1 1 0; text-align: center;">
                    <p style="margin: 0;"><strong>{records.count()}</strong></p>
                </div>
                <div style="flex: 1 1 0; text-align: center;">
                    <p style="margin: 0;"><strong>{round(concentration, 2)}</strong></p>
                </div>
                <div style="flex: 1 1 0; text-align: center;">
                    <p style="margin: 0;"><strong>{round(absorbance, 2)}</strong></p>
                </div>
            </div>
        </div>
        '''
        
        # For filling the color and opacity on the bounded geojson
        folium.GeoJson(
            geojson,
            style_function=lambda feature: {
                'fillColor': 'red',
                'color': 'red',
                'weight': 1,
                'fillOpacity': (1-concentration/40)
            }
        ).add_to(map)

        # For putting the marker on the bounded geojson
        folium.Marker(
            location=center, 
            popup=folium.Popup(popup, max_width=300),
            icon=folium.Icon(icon='info-sign', color='blue')
        ).add_to(map)

# Location Page Function
@login_required(login_url='/login')
def location(request, antibiotics="All", division="Region"):
    # For setting the assigned details to be shown on the map
    if request.method == "POST":
        division = request.POST.get('location_division')
        antibiotics = request.POST.get('location_antibiotics')

    _, default_center = center_geojson("NCR")
    map = folium.Map(location=default_center, zoom_start=7)
    records = Records.objects.filter(user=request.user)

    # For plotting the specified location and details based on the division (region, province, municipality)
    if division == "Region":
        # Sort all the record details by the same region
        for name in list(set(records.values_list('region', flat=True).distinct())):
            region_geojson, region_center = center_geojson(name)
            records_region = records.filter(region=name)
            records_region = records_region.filter(antibiotics=antibiotics) if antibiotics != "All" else records_region
            map_geojson(map, records_region, region_geojson, region_center, name, antibiotics)
    elif division == "Province":
        # Sort all the record details by the same province
        for region, province in list(set(records.values_list('region', 'province').distinct())):
            province_geojson, province_center = center_geojson(province + ', ' + region)
            records_province = records.filter(region=region, province=province)
            records_province = records_province.filter(antibiotics=antibiotics) if antibiotics != "All" else records_province
            map_geojson(map, records_province, province_geojson, province_center, province + ', ' + region, antibiotics)
    elif division == "Municipality":
        # Sort all the record details by the same municipality
        for region, province,municipality in list(set(records.values_list('region', 'province', 'municipality').distinct())):
            municipality_geojson, municipality_center = center_geojson(municipality + ", " + province + ', ' + region)
            records_municipality = records.filter(region=region, province=province, municipality=municipality)
            records_municipality = records_municipality.filter(antibiotics=antibiotics) if antibiotics != "All" else records_municipality
            map_geojson(map, records_municipality, municipality_geojson, municipality_center, municipality + ", " + province + ', ' + region, antibiotics)

    template_name = "natrosensor/location/page.html"
    map.add_child(folium.LatLngPopup())

    fig = branca.element.Figure(height='100%')
    fig.add_child(map)
    map_embed = fig._repr_html_()
    return render(request, template_name, context={"template_name": "Location", "map": map_embed, "antibiotics": antibiotics, "division": division})

# Dashboard Page Function
@login_required(login_url='/login')
def dashboard(request):
    first_name = request.user.first_name if request.user.is_authenticated else "User"

    # Getting the recent record
    recent = Records.objects.filter(user=request.user).first()

    # Getting the upcoming event schedule
    events = Event.objects.filter(user=request.user).filter(date__gte=timezone.now().date())

    # Getting the total user of the website
    user_count = User.objects.all().count() 

    # Getting the total process made by the user
    process_count = Records.objects.filter(user=request.user).count()   
    process = {}

    # Get the number of processes within the last 15 days
    today = datetime.today()
    for index in range(15, 0, -1):
        start = today - timedelta(days=index-1)
        # Get all the records details based on date
        proc = Records.objects.filter(user=request.user).filter(created_at__date=start)
        process[timezone.localdate(timezone.make_aware(start)).strftime("%b %d")] = proc.count()
    
    # Get the maximum number of processes within the last 15 days
    max_count = max(process.values())
    template_name = "natrosensor/dashboard/page.html" if request.headers.get('HX-Request') else "natrosensor/dashboard/loading.html"   

    return render(request, template_name, context={"template_name": "Dashboard", "first_name": first_name, "process_count": process_count, "user_count": user_count, "recent": recent, "process": process, "events": events, "max": max_count})

# Process Page Function
@login_required(login_url='/login')
def process(request):
    # When the user processes the details
    if request.method == "POST":
        process_file = request.FILES['process_file']   

        # Set all the process details to the process variable
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

        response = JsonResponse({"success": True})
        response["HX-Redirect"] = "/result"
        return response

    template_name = "natrosensor/process/page.html"
    return render(request, template_name, context={"template_name": "Process", "location": LOCATION, "antibiotics": ANTIBIOTICS})

# Records Page Function
@login_required(login_url='/login')
def records(request):
    search = request.GET.get('search', None)
    records = Records.objects.filter(user=request.user)

    page_number = request.GET.get('page')
    paginator = Paginator(records, 7)
    page_obj = paginator.get_page(page_number)
    success = request.session.pop("success", False)

    template_name = "natrosensor/records/page.html"
    return render(request, template_name, context={"template_name": "Records", "records": page_obj, "headers": ["Name", "Date", "Time", "Antibiotics", ""], "success": success})

# Delete specific record by ID Function
@login_required(login_url='/login')
def delete_record(request, id):
    # Get the specific record details regardless if it is empty or not
    item = get_object_or_404(Records, pk=id, user=request.user)

    # When the user deleting the specific record
    if request.method == 'POST':
        # Delete the specific record
        item.delete()
        request.session["success"] = True

        # Set the modification of the session to True (for ensuring the details to be fully deleted in the system)
        request.session.modified = True
        return JsonResponse({"success": True})

# Schedule Page Function
@login_required(login_url='/login')
def schedule(request):
    # When the user creates the event
    if request.method == "POST":
        # Obtain all the event details and assign each to a variable
        name = request.POST.get('event_name')
        date = request.POST.get('event_date')
        time = request.POST.get('event_time')
        detail = request.POST.get('event_detail')
        
        # Create the new event
        event = Event(name=name, date=date, time=time, detail=detail, user=request.user)
        event.save()

        return JsonResponse({"success": True})
    
    # Assign the value of month a year from the current calendar shown
    month = request.GET.get('month', datetime.today().month)
    year = request.GET.get('year', datetime.today().year)

    # Check if the value of the month is on out of range
    # If the value of month is 13
    if int(month) > 12:
        # Set the year added by 1 and the month will be set to 1
        year = str(int(year) + 1)
        month = str(1)
    # If the value of month is 0
    elif int(month) < 1:
        # set the year subracted to 1 and the month will be set to 12
        year = str(int(year) - 1)
        month = str(12)

    # Get the event details from the user based on year and month
    events = Event.objects.filter(user=request.user, date__year=year, date__month=month)

    # Check the days of the specified month and year
    total_days = monthrange(int(year), int(month))[1]

    # Set all the days of the specified month and year to False
    days_with_events = {day: False for day in range(1, total_days + 1)}

    # For checking if that specific date contains the event details
    for event in events:
        days_with_events[event.date.day] = True

    template_name = "natrosensor/schedule/page.html"
    return render(request, template_name, context={"template_name": "Schedule", "events": events, "days_with_events": json.dumps(days_with_events), "year": int(year), "month": int(month)})

# Delete Event Function
@login_required(login_url='/login')
def delete_schedule(request, id):
    # Get the specific event details regardless if it is empty or not
    item = get_object_or_404(Event, pk=id, user=request.user)
    # When the user clicks the delete button
    if request.method == "POST":
        # Delete the specified event 
        item.delete()
        request.session["success"] = True

        # Set the session request to be modified
        request.session.modified = True
        return JsonResponse({"success": True})

# Show Event Function (from a specified date)
@login_required(login_url='/login')
def show_schedule(request):
    date = request.GET.get('date')
    page_number = request.GET.get('page')

    # Get the event details from the user based on date
    events = Event.objects.filter(user=request.user, date=datetime.strptime(date, "%B %d, %Y").date())

    # Paginate all the event details by 8 and get the specific event details depending on the page number
    paginator = Paginator(events, 8)   
    page_obj = paginator.get_page(page_number)

    template_name = "natrosensor/schedule/view.html"
    return render(request, template_name, context={"events": page_obj, "headers": ["Name", "Date", "Time", "Details", ""]})

# About Page Function
@login_required(login_url='/login')
def about(request):
    template_name = "natrosensor/about/page.html"
    context = {"template_name": "About", "project_leader": PROJECT_LEADER, "project_staff": PROJECT_STAFF}
    return render(request, template_name, context)

# Profile Page Function
@login_required(login_url='/login')
def profile(request):
    # Check if the user is logged in
    user = request.user if request.user.is_authenticated else None

    # Check if the user is done editing the profile details 
    if request.method == "POST":
        first_name = request.POST.get("first_name", user.first_name)
        last_name = request.POST.get("last_name", user.last_name)
        institution = request.POST.get("institution", user.institution)

        # Assign the new details to the assigned user
        user.first_name = first_name
        user.last_name = last_name
        user.institution = institution
        user.save()

        return JsonResponse({"success": True})   

    # For checking the number of process within the last 30 days
    process = {}
    today = datetime.today()
    # For every date within the last 30 days
    for index in range(30, 0, -1):
        start = today - timedelta(days=index-1)
        # Check the records within the specific date
        proc = Records.objects.filter(user=request.user).filter(created_at__date=start)

        # Get the total number of records obtained from the specified date
        process[timezone.localdate(timezone.make_aware(start)).strftime("%b %d")] = proc.count()
    
    # Determine the date containing the maximum count of the process within the last 30 days
    max_count = max(process.values())
    template_name = "natrosensor/profile/page.html"
    return render(request, template_name, context={"template_name": "Profile", "user": user, "process": process, "max": max_count})

# Setting Page Function
@login_required(login_url='/login')
def settings(request):
    template_name = "natrosensor/settings/page.html"
    return render(request, template_name, context={"template_name": "Settings"})

# Result Function
@login_required(login_url='/login')
def result(request):
    # Get all the needed inputs to the assigned variable
    process = request.session.get('process')
    graph = request.session.get('graph')
    y_int = request.session.get('y_int')
    slope = request.session.get('slope') 
    c50 = request.session.get('c50')
    c50_y = request.session.get('c50_y')
    lod = request.session.get('lod')

    # When the user saves the process
    if request.method == "POST":
##==> Correction to record data input per location
        concentration_lr = request.POST.get('concentration_lr', '').strip()
        absorbance_lr = request.POST.get('absorbance_lr', '').strip()
        if concentration_lr:
            try:
                concentration_value = float(concentration_lr)
                absorbance_value = float(absorbance_lr)
            except ValueError:
                concentration_value = c50
                absorbance_value = c50_y
        else:
            concentration_value = c50
            absorbance_value = c50_y
##==>
        # Create and save new record from all the process details
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
            #concentration=c50, #c50
            #absorbance=c50_y
            ##==>
            concentration=concentration_value, #Antibiotic dosage (ppm), as computed using Linear regression
            absorbance=absorbance_value, #DPV peak current input (uA)
            ##==>
            user=request.user
        )
        new_result.save()
        request.session.modified = True
        return JsonResponse({"success": True})
    
    template_name = "natrosensor/result/page.html"
    return render(request, template_name, context={"template_name": "Result", "graph": graph, "y_int": round(y_int, 4), "slope": round(slope, 4), "c50": c50, "c50_y": c50_y, "process": process})

# When the user accessing invalid routes, the not found page will show up
def not_found(request, exception=None):
    # Check if the user is logged in
    is_authenticated = True if request.user.is_authenticated else False
    template_name = "natrosensor/error/page_404.html"
    return render(request, template_name, context={"is_authenticated": is_authenticated}, status=404)