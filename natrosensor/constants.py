import pandas as pd
import os

LOCATION = {
    'region': pd.read_csv(os.path.join(os.path.dirname(__file__), "module/csv/table_region.csv")).to_dict('split')['data'],
    'province': pd.read_csv(os.path.join(os.path.dirname(__file__), "module/csv/table_province.csv")).to_dict('split')['data'],
    'municipality': pd.read_csv(os.path.join(os.path.dirname(__file__), "module/csv/table_municipality.csv")).to_dict('split')['data'],
    'barangay': pd.read_csv(os.path.join(os.path.dirname(__file__), "module/csv/table_barangay.csv")).to_dict('split')['data']
}

PROJECT_LEADER = {
    "image": "rlr-300x300.png",
    "name": "Resmond L. Reaño, PhD",
    "position": "Assistant Professor / Project Leader"
}

PROJECT_STAFF = [
    ["grp-300x300.png", "Glenson R. Panghulan, MSc", "Assistant Professor"],
    ["frcb-300x300.png", "Felix Rey C. Bueta, MSc", "Assistant Professor"],
    ["dwlbl-300x300.png", "Donna Wren B. Libunao-Bueta, MSc", "Assistant Professor"],
    ["ileg-300x300.png", "Ian Lorenzo E. Gonzaga, MSc", "Assistant Professor"],
    ["IOMagculang.png", "Ismael O. Magculang, MSc", "Project Technical Assistant III"],
    ["VPLaguardia.png", "Vincent Paul P. Laguardia", "Project Technical Assistant III"],
    ["JTTagaza.png", "Joreyn Angelo T. Tagaza", "Project Technical Assistant II"],
    ["ACTorres.png", "Angelo C. Torres", "Project Technical Aide V"],
    ["CRTumambing.png", "Caren R. Tumambing", "Project Technical Assistant III"],
    ["MBGalanido.png", "Marjhun Christianee B. Galanido", "Project Technical Assistant II"]
]

SIDEBAR_MENU = [
    ["Dashboard", "Process", "Records", "Location", "Schedule", "About"],
    ["Profile", "Settings", "Logout"]
]

ANTIBIOTICS = [
    "Azithromycin",
    "Ciprofloxacin",
    "Metronidazole",
    "Penicillin"
]

ADMIN_REGION = "3"
ADMIN_PROVINCE = "4"
ADMIN_MUNICIPALITY = "6"
