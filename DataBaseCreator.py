import sqlite3 as sl
import requests
import json
import geopy.distance as gd
import argparse
import os.path

# Вспомогательные классы
class Station:
    def __init__(self):
        self.id = 0
        self.line_id = 0
        self.name = ''
        self.order = 0
        self.lat = 0.
        self.lng = 0.
    def __str__(self):
        return self.name

class Line:
    def __init__(self):
        self.id = 0
        self.name = ''
        self.city_id = 0
        self.color = 0
    def __str__(self):
        return self.name

parser = argparse.ArgumentParser(description='Creates/appends database of metro lines, stations and routes')
parser.add_argument('--api_city_id', type=int, help='City id for api.hh.ru/metro')
parser.add_argument('--db_dir', type=str, help='Database directory (with file name)')
parser.add_argument('--create_new', type=bool,default=False, help='If "True" database will be created or rewritten (default: False)')
args = parser.parse_args()

api_city_id = args.api_city_id
db_dir = args.db_dir

# получение данных
response = requests.get('https://api.hh.ru/metro/' + str(api_city_id))
content = response.content
data = json.loads(content)

city = data['name']

con = None
cursor = None

if args.create_new:
    if os.path.exists(db_dir):
        os.remove(db_dir)
        print('Removed old db')

    # creating new database
    con = sl.connect(db_dir)
    print('Created db file')
    cursor = con.cursor()
    cursor.execute(
        """create table cities
        (
            id        INTEGER
                primary key autoincrement,
            city_name TEXT not null
                unique
        );""")
    con.commit()
    print('Created table "cities"')
    cursor.execute(
        """create table lines
        (
            id         INTEGER
                primary key autoincrement,
            line_name  TEXT    not null,
            color      INT default 0,
            city_id_FK INTEGER not null
                references cities
        );""")
    con.commit()
    print('Created table "lines"')
    cursor.execute(
        """create table stations
        (
            id            INTEGER
                primary key autoincrement,
            name          TEXT    not null,
            latitude      REAL    not null,
            longitude     REAL    not null,
            station_order INTEGER not null,
            line_id_FK    INTEGER not null
                references lines,
            check (station_order >= 0)
        );""")
    con.commit()
    print('Created table "stations"')
    cursor.execute(
        """create table neighboring
            (
                id                   INTEGER
                    primary key autoincrement,
                first_station_id_FK  INTEGER not null
                    references stations,
                second_station_id_FK INTEGER not null
                    references stations,
                approximate_time     INTEGER not null
    );""")
    con.commit()
    print('Created table "neighboring"')
else:
    con = sl.connect(db_dir)
    print("Connected to db")
    cursor = con.cursor()

try:
    cursor.execute("""INSERT INTO cities (city_name) VALUES (?)""",[(city)])
    con.commit()
    print(f"inserted city {city} to table")
except:
    pass

city_id = cursor.execute(
    """SELECT id FROM cities
        WHERE city_name = ?""", [(city)]).fetchall()[0][0]

stations = []
lines = []

# Добавляем в таблицу все линии и станции
for line in data['lines']:
    ln = Line()
    ln.name = line['name']
    ln.color = int(line['hex_color'],16)
    ln.city_id = city_id
    values = [ln.name,ln.city_id,ln.color]
    cursor.execute(
        """INSERT INTO lines (line_name, city_id_FK, color)
            VALUES (?,?,?)""", values)
    con.commit()
    ln.id = cursor.lastrowid
    lines.append(ln)
    for station in line['stations']:
        if station['name'] == 'Зенит':
            continue

        st = Station()

        if city == 'Санкт-Петербург' and station['name'] == 'Новокрестовская':
            st.name = 'Зенит'
        else:
            st.name = station['name']

        st.lat= float(station['lat'])
        st.lng = float(station['lng'])
        st.order = int(station['order'])
        st.line_id = ln.id
        values = [st.name,st.lat,st.lng,st.line_id,st.order]
        cursor.execute(
            """INSERT INTO stations (name, latitude, longitude,line_id_FK, station_order)
                VALUES (?,?,?,?,?)""", values)
        con.commit()
        st.id = cursor.lastrowid
        stations.append(st)
print("lines and stations added")
# km/h
train_speed = 50;

# Считаем время для соседних станций одной линии
for line in lines:
    current_line_stations = list(filter(lambda s: s.line_id == line.id, stations))
    current_line_stations.sort(key=lambda s: s.order)
    prev_station = None
    for station in current_line_stations:
        if prev_station == None:
            prev_station = station
            continue
        route = [prev_station, station]
        prev_station_coord = (prev_station.lat, prev_station.lng)
        station_coord = (station.lat, station.lng)
        distance = gd.distance(prev_station_coord, station_coord).km
        approximate_time = round(distance / train_speed * 60 * 60) # in seconds
        values = [route[0].id,route[1].id,approximate_time]
        cursor.execute(
            """
            INSERT INTO neighboring (first_station_id_FK, second_station_id_FK, approximate_time)
            VALUES (?, ?, ?)
            """, values
        )
        con.commit()

        route.reverse()
        values = [route[0].id, route[1].id, approximate_time]
        cursor.execute(
            """
            INSERT INTO neighboring (first_station_id_FK, second_station_id_FK, approximate_time)
            VALUES (?, ?, ?)
            """, values
        )
        con.commit()
        prev_station = station

print("added time between stations")

# km/h
human_speed = 18

for main_station in stations:
    for transfer_station in list(filter(lambda s:s.line_id != main_station.line_id ,stations)):
        main_coord = (main_station.lat, main_station.lng)
        transfer_coord = (transfer_station.lat, transfer_station.lng)
        distance = gd.distance(main_coord, transfer_coord).km
        if distance < 0.3:
            route = [main_station, transfer_station]
            approximate_time = round(distance / human_speed * 60 * 60)
            values = [route[0].id, route[1].id, approximate_time]
            cursor.execute(
                """
                INSERT INTO neighboring (first_station_id_FK, second_station_id_FK, approximate_time)
                VALUES (?, ?, ?)
                """, values
            )
            con.commit()

print("added transfers time")
con.close()
print("Done!");