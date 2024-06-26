from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout 
from django.contrib.auth.decorators import login_required
# import folium, geocoder
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt

# from scipy.optimize import curve_fit
from io import StringIO
from .forms import SignupForm, LoginForm

def web_main(request):
    return redirect('/natrosensor/login')

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)    
                return redirect('/natrosensor/dashboard')
    else:
        form = LoginForm()

    template_name = "natrosensor/login.html"
    return render(request, template_name, context={"template_name": "Login", 'form': form})

def user_logout(request):
    logout(request)
    return redirect('/natrosensor/login')

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
                return redirect('/natrosensor/login')
    else:
        form = SignupForm()

    template_name = "natrosensor/signup.html"
    return render(request, template_name, context={"template_name": "Signup", 'form': form})

@login_required(login_url='/natrosensor/login')
def location(request):
    template_name = "natrosensor/location.html"
    return render(request, template_name, context={"template_name": "Location"})
    # g = geocoder.ip('me')
    # map = folium.Map(location=g.latlng, zoom_start=12)
    # folium.Marker(g.latlng, popup=g.address,icon=folium.Icon(color='blue', icon='crosshairs', prefix='fa')).add_to(map)
    # map = map._repr_html_()
    # return render(request, template_name, context={"template_name": "Location", "map": map, "location": g})

@login_required(login_url='/natrosensor/login')
def dashboard(request):
    user = {}
    user['first_name'] = request.user.first_name if request.user.is_authenticated else None
    user['last_name'] = request.user.last_name if request.user.is_authenticated else None

    template_name = "natrosensor/dashboard.html"
    return render(request, template_name, context={"template_name": "Dashboard", "user": user})

@login_required(login_url='/natrosensor/login')
def process(request):
    template_name = "natrosensor/process.html"
    return render(request, template_name, context={"template_name": "Process"})

@login_required(login_url='/natrosensor/login')
def records(request):
    template_name = "natrosensor/records.html"
    return render(request, template_name, context={"template_name": "Records"})

@login_required(login_url='/natrosensor/login')
def about(request):
    template_name = "natrosensor/about.html"
    return render(request, template_name, context={"template_name": "About"})

@login_required(login_url='/natrosensor/login')
def profile(request):
    template_name = "natrosensor/profile.html"
    return render(request, template_name, context={"template_name": "Profile"})

@login_required(login_url='/natrosensor/login')
def settings(request):
    template_name = "natrosensor/settings.html"
    return render(request, template_name, context={"template_name": "Settings"})

@login_required(login_url='/natrosensor/login')
def result(request):
    process_name = request.POST.get('process_name', '') 
    process_trial = int(request.POST.get('process_trial', ''))
    process_file = request.FILES['process_file']

    df = pd.read_csv(process_file)

    x_data = df.iloc[:,0]
    log_x = np.log10(x_data)
    y_data = df.iloc[:,2]

    params, covariance = curve_fit(hill_model, log_x, y_data, p0=[min(y_data), max(y_data), np.median(log_x), 1.0])

    r_min, r_max, ec50, slope = params

    x_model = np.linspace(min(log_x), max(log_x), 100)
    y_model = hill_model(x_model, r_min, r_max, ec50, slope)

    residuals = y_data - hill_model(log_x, r_min, r_max, ec50, slope)
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y_data-np.mean(y_data))**2)
    r_squared = 1 - (ss_res / ss_tot)
    print(r_squared)

    fig = plt.figure()
    plt.scatter(log_x, y_data)
    plt.plot(x_model, y_model)
    plt.rcParams["font.family"] = "Times New Roman" # set the font of the graph to Times New Roman

    plt.xlabel("Concentration")
    plt.ylabel("Response (mV)")
    plt.xticks(ticks=log_x, labels=x_data) 

    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    graph = imgdata.getvalue()    

    template_name = "natrosensor/result.html"
    return render(request, template_name, context={"template_name": "Result", "graph": graph})

def hill_model(x, r_min, r_max, ec50, slope):
    return r_min + (r_max - r_min) / (1 + np.exp(-1 * slope * (x - ec50)))

def linear_model(x, slope, b):
    return (x * slope) + b
