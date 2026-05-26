import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from scipy import interpolate
from scipy.optimize import curve_fit

matplotlib.use('agg')

# Function for 4PL Logistic Curve
    # r_min - min value (a)
    # slope - Hills slope (b)
    # ec50 - point of inflection (EC50) (c)
    # r_max - max value (d)

def fourpl(dataframe, size):
    x_data = dataframe.iloc[:,0]
    y_data = dataframe.iloc[:,1]

    #x_data = np.log10(x_data)*-1

    #Perform the estimation of the parameters r_min, slope, ec50, and r_max
    #Estimate intial p0
    p0_est = [max(y_data), 1.0, np.median(x_data), min(y_data)]
    bounds = (0, [np.inf, 10, np.inf, np.inf])
    popt, pcov = curve_fit(fourpl_model, x_data, y_data, p0=p0_est, bounds=bounds)

    a_f = popt[0]
    b_f = popt[1]
    c_f = popt[2]
    d_f = popt[3]

    #Computation of R-squared
    r_squared = get_rsquared(x_data, y_data, popt)

    #Identify EC50 and its position
    c50, c50_y = get_c50(popt)

    #Identify the Limit of detection (LOD)
    lod = get_lod(x_data, y_data, popt)[0]

    x_model = np.linspace(min(x_data), max(x_data), 500)
    y_model = fourpl_model(x_model, *popt)

    fig = plt.figure()
    plt.plot(x_data, y_data, 'o', markersize = 8, mfc = 'none', color = 'blue')
    plt.plot(x_model, y_model, color='black', linewidth=2, label=f'4PL Model Fit, R\u00b2 = {r_squared:.2f}')

    plt.xscale('log')
    plt.xlabel("Antibiotic Dosage, ppm")
    plt.ylabel("Peak current, µA")
    plt.title('DPV Peak Current vs Antibiotic Dosage (4PL Model)')

    #Annotate the EC50
    plt.axvline(c50, color = 'green', linestyle='--', label=f'EC50 = {c50:.2f} ppm')
    #Annotate LOD
    if not np.isnan(lod):
         plt.axvline(lod, color = 'orange', linestyle='--', label=f'Detection Limit = {lod:.2f} ppm')

    plt.legend()

    #Create a linear equation from lod to r_max
    #Define the LLOQ
    sd_blank = get_lod(x_data, y_data, popt)[1]
    y_lloq = a_f - 10*sd_blank
    y_lod = a_f - 3*sd_blank

    lod_conc = inv_4PL(y_lod, *popt)
    lloc_conc = inv_4PL(y_lloq, *popt)

    #Define the ULOQ
    uloq_conc = np.max(x_data)
    y_uloq = fourpl_model(uloq_conc, *popt)

    #Create the Linear Equation y=mx + b, where m is the Hill's slope
    #Since DPV current decreases with concentration, m is negative
    m_ = -b_f

    #solve for the y-intercept, b
    y_int = y_lloq - (m_ * lloc_conc)

    return FigureCanvas(fig), y_int, m_, c50, c50_y

#Get the 4PL logistic curve 
# y = d + (a - d) / (1 + (x / c)**b)
# a: Maximum asymptote (Top) r_max
# d: Minimum asymptote (Bottom) r_min
# c: EC50 (Inflection point)
# b: Hill slope (Steepness)
def fourpl_model(x, r_max, slope, ec50, r_min):
    return r_min + ((r_max - r_min) / (1 + (x / ec50) ** slope))

#Inverse 4PL
def inv_4PL(y, r_max, slope, ec50, r_min):
    if y >= r_max:
        return 0.0
    if y <= r_min:
        return np.inf
    val = ((r_max - r_min) / (y - r_min)) - 1
    
    if val < 0:
        return np.nan
    return ec50 * (val**(1/slope))

def get_rsquared(x_data, y_data, popt):
    residuals = y_data - fourpl_model(x_data, *popt)
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)

    #print(f'The value of R_squared is {r_squared}')
    return r_squared

def get_c50(popt):
    c50 = popt[2]
    c50_y = fourpl_model(c50, *popt)
    #print(f'The value of the half maximal effective concentration is {c50}.')
    return c50, c50_y

def get_lod(x_d, y_d, params):
    residuals = y_d - fourpl_model(x_d, *params)
    sd_blank = np.std(residuals)

    a_fit = params[0]
    b_fit = params[1]
    c_fit = params[2]
    d_fit = params[3]
    y_lod = a_fit - 3*sd_blank

    if y_lod > d_fit:
         lod = c_fit*(((a_fit-d_fit)/(y_lod-d_fit))-1)**(1/b_fit)

    else:
         lod = np.nan #Signal is too low to resolve from background
    
    #print(f'The detection limit is {lod} ppm.')
    return lod, sd_blank

def graph_settings():
    size = 16
    return size