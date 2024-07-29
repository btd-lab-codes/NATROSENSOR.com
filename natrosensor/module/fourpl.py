import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy import interpolate
from scipy.optimize import curve_fit

matplotlib.use('agg')

# Function for 4PL Logistic Curve
    # r_min - min value (a)
    # slope - Hills slope (b)
    # ec50 - point of inflection (EC50) (c)
    # r_max - max value (d)

def fourpl(dataframe, size):
    x_data = dataframe.iloc[:,2]
    y_data = dataframe.iloc[:,3]

    x_data = np.log10(x_data)*-1

    #Perform the estimation of the parameters r_min, slope, ec50, and r_max
    popt, pcov = curve_fit(fourpl_model, x_data, y_data, p0=[0,1,1,1])

    #Computation of R-squared
    r_squared = get_rsquared(x_data, y_data, popt)

    c50, c50_y, kd = get_c50(popt)

    x_model = np.linspace(min(x_data), max(x_data), 100)
    y_model = fourpl_model(x_model, *popt)

    print('Four parameter logistic model')
    print(f'a = {popt[0]}')
    print(f'b = {popt[1]}')
    print(f'c = {popt[2]}')
    print(f'd = {popt[3]}')

    fig = plt.figure()
    plt.plot(x_data, y_data, 'o', markersize = 10, mfc = 'none', color = 'black')
    plt.plot(x_model, y_model, color='black')
    plt.xlabel("H1 concentration, nM")
    plt.ylabel("Absrobance 450 nm")
    plt.annotate("C50", xy = (c50, c50_y), xytext = (c50, c50_y + 0.1), arrowprops = dict(arrowstyle = "->"), color = 'b', weight = 'bold', ha='center', size = size * 1.15)
    plt.hlines(c50_y, c50, len(x_data) + 0.5, linestyle="dashed", color = "b")
    plt.vlines(c50, 0, c50_y, linestyle="dashed", color="b")

    x_data.to_numpy()
    ticks = 10**(-x_data)

    v = [-0.5, 6.5, 0.2, 0.7]
    plt.axis(v)
    plt.xticks(np.arange(7), ticks)
    plt.gca().invert_xaxis()

    # plt.imshow(np.log(np.abs(pcov)))
    # plt.colorbar()

    #Creating a tangent line to c50
    x_0 = c50
    tck = interpolate.splrep(x_model, y_model)
    y_0 = interpolate.splev(x_0, tck)
    dydx = interpolate.splev(x_0, tck, der=1)

    tangent = lambda x: dydx*x + (y_0-dydx*x_0)

    #Plot the tangent line
    x_plot = np.linspace(4.5,1,50)
    #plt.plot(x_plot, tangent(x_plot), linestyle = "dashed", color = 'blue')

    popt_l, pcov_l = curve_fit(model_, x_plot, tangent(x_plot), p0=[1,0.1])

    print(f'The LR has a formula: y = {popt_l[0]} + {popt[1]}.')

    return fig, popt_l[0], popt[1]

#Get the 4PL logistic curve 
def fourpl_model(x, r_min, slope, ec50, r_max):
    return r_max + ((r_min - r_max) / (1 + (x / ec50) ** slope))

#Get the slope and intercept of the LR for LOD calculation
def model_(x_, m_, int_):
        return m_*x_+int_

def get_rsquared(x_data, y_data, popt):
    residuals = y_data - fourpl_model(x_data, *popt)
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)

    print(f'The value of R_squared is {r_squared}')
    return r_squared

def get_c50(popt):
    c50 = popt[2]
    kd = 10 ** (-c50)
    c50_y = fourpl_model(c50, *popt)

    print(f'The value of the half maximal effective concentration is {c50}.')
    print(f'The corresponding absorbance is {c50_y}.')
    print(f'The Kd value is {kd} nM.')
    return c50, c50_y, kd

def graph_settings():
    size = 16
    params = {'font.family': 'Times New Roman',
            'legend.fontsize': 'x-large',
            'figure.figsize': (8,6), 
            'figure.dpi': 100,
            'axes.labelsize': size,
            'axes.titlesize': size,
            'xtick.labelsize': size*0.95,
            'ytick.labelsize': size*0.95,
            'axes.titlepad': 40}
    
    plt.rcParams.update(params)
    return size