from datetime import datetime, timedelta
import ephem
import getpass
from pathlib import Path
from spacetrack import SpaceTrackClient
import urllib.request
import json

# http://rhodesmill.org/pyephem/tutorial.html#loading-bodies-from-catalogues
now = datetime.now()


def init():
    """
    Initialize credits and satellite list
    starts program
    """
    spacetrack_login = Path("./credits.txt")
    if not spacetrack_login.is_file():
        print("Please enter your credentials for space-track.org")
        store_credits()

    credit_list = load_credits()
    st = SpaceTrackClient(credit_list[0].replace("\n", ""), credit_list[1].replace("\n", ""))

    satellite_file = Path("./satellitelist.json")
    if not satellite_file.is_file():
        print("Downloading satellite list. Please wait ...")
        satellite_list(st)
        print("Download finished.")
    track_times(st)


def satellite(st):
    """
    Select satellite
    Calculate TLE
    :param st: SpaceTrackClient
    :return:
    """
    query_satellite = input("Satellite: ")

    satellite_json = open("./satellitelist.json", "r")
    data_json = json.loads(satellite_json.read())

    norad_id_list = []
    for x in range(0, len(data_json)):
        if query_satellite.lower() in str(data_json[x]['SATNAME']).lower():
            norad_id_list.append([data_json[x]['SATNAME'], data_json[x]['NORAD_CAT_ID']])

    satellite_json.close()

    for idx, x in enumerate(norad_id_list):
        print(idx, ": ", x[0])

    selected_satellite = 0
    if len(norad_id_list) > 1:
        selected_satellite = int(input("Number: "))

    cat_id = [int(norad_id_list[selected_satellite][1])]

    print("Satellite: ", norad_id_list[selected_satellite][0])

    data = st.tle_latest(norad_cat_id=cat_id, ordinal=1, format='3le')
    tle = data.split("\n")
    print(tle)

    if tle[0] is not '':
        sat = ephem.readtle(tle[0], tle[1], tle[2])
        return sat


def satellite_list(st):
    """
    Get list of all satellites
    :param st: SpaceTrackClient
    """
    file = open("satellitelist.json", "w")
    data = st.satcat(orderby='launch desc', format='json')
    for x in data.split(","):
        if x[0] is "\"":
            file.write("\t")
        file.write(x)
        if ']' not in x:
            file.write(",\n")

    file.close()


def ground_station():
    """
    Search on OSM for location
    Set observer
    :return: Observer
    """
    ground = ephem.Observer()

    query_str = input("Location:  ")
    url_str = "https://nominatim.openstreetmap.org/search/" + query_str.replace(" ", "%20") + "?format=json"

    with urllib.request.urlopen(url_str) as url:
        data = json.loads(url.read().decode())
        if not data:
            return;
        ground.lat, ground.lon = data[0]['lat'], data[0]['lon']
        print(data[0]['display_name'] + "\n")

    return ground


def track_times(st):
    """
    Configure satellite and ground station
    Calculate rise and set of satellite relative to ground station
    :param st: SpaceTrackClient
    """
    sat = satellite(st)
    if not sat:
        print("Unable to calculate times.")
        return

    ground = ground_station()
    if not ground:
        print("Unable to find ground station.")
        return

    result_list = []

    for x in range(0, 24):
        ground.date = now + timedelta(hours=x)
        sat.compute(ground)
        result = [str(sat.rise_time), str(sat.transit_time), str(sat.set_time)]
        if result not in result_list:
            result_list.append(result)

    for x in result_list:
        print("Rise    %s" % x[0])
        print("Transit %s" % x[1])
        print("Set     %s\n" % x[2])


def store_credits():
    """
    Store credits in file
    """
    email = input("E-Mail: ")
    password = getpass.getpass()

    file = open("credits.txt", "w")
    file.write(email + "\n")
    file.write(password)
    file.close()


def load_credits():
    """
    Load credits from file
    :return: list with login information
    """
    result_list = []
    with open('credits.txt') as fp:
        for line in fp:
            result_list.append(line)
    return result_list


init()
