from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt
import dateutil
# Python SQL toolkit and Object Relational Mapper
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

resource_url = "Resources/hawaii.sqlite"
engine = create_engine(f"sqlite:///{resource_url}")
# prepare base
Base = automap_base()
Base.prepare(engine, reflect=True)
# View all of the classes that automap found
Base.classes.keys()
# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station
def init():
    # create engine to hawaii.sqlite
    resource_url = "Resources/hawaii.sqlite"
    engine = create_engine(f"sqlite:///{resource_url}")
    # prepare base
    Base = automap_base()
    Base.prepare(engine, reflect=True)
    # View all of the classes that automap found
    Base.classes.keys()
    # Save references to each table
    Measurement = Base.classes.measurement
    Station = Base.classes.station
    # Create our session (link) from Python to the DB
    session = Session(engine)
    return session

session = init()
# Find the most recent date in the data set.
recent_dates = session.query(Measurement.date).order_by(Measurement.date.desc())
last = recent_dates.first()[0]
last
# Find when 12 months from most recent is
last_date = dt.datetime.strptime(last, '%Y-%m-%d').date()
delta = dateutil.relativedelta.relativedelta(months=-12)
past = last_date+delta
past
# Design a query to retrieve the last 12 months of precipitation data and plot the results. 
# Starting from the most recent data point in the database. 
prcp_df = pd.read_sql(session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= past).statement, session.bind)\
    .set_index('date')\
        .dropna()\
            .sort_index()

fig, ax = plt.subplots()
# Use Pandas Plotting with Matplotlib to plot the data
plt.bar(x = prcp_df.index, height=prcp_df['prcp'], width=1)
ax.xaxis.set_major_locator(plt.MaxNLocator(6))
prcp_df.describe()
# Design a query to calculate the total number of stations in the dataset
session.query(Station).count()
# Design a query to find the most active stations (i.e. what stations have the most rows?)
# List the stations and the counts in descending order.
stat_count = func.count(Measurement.station)
station_activity = session.query(Measurement.station, stat_count).group_by(Measurement.station).order_by(stat_count.desc()).all()
station_activity
# Using the most active station id from the previous query, calculate the lowest, highest, and average temperature.
most_active = station_activity[0][0]
session.query(func.min(Measurement.tobs),\
     func.max(Measurement.tobs),\
          func.avg(Measurement.tobs))\
              .filter(Measurement.station == most_active)\
                  .first()
# Using the most active station id
# Query the last 12 months of temperature observation data for this station and plot the results as a histogram
last_year_data = session.query(Measurement.tobs).filter(Measurement.station == most_active, Measurement.date >= past).all()
last_year_df = pd.DataFrame(last_year_data)
last_year_df.plot(kind='hist')
# Close Session
session.close()

from flask import Flask, jsonify

app = Flask(__name__)

routes = [
    "/",
    "/api/v1.0/precipitation",
    "/api/v1.0/stations",
    "/api/v1.0/tobs",
    "/api/v1.0/<start>/<end>"
]

@app.route("/")
def index():
    message = "Available Routes:\n"
    for route in routes:
        message+= f'<p>{route}</p>'
    return message


@app.route("/api/v1.0/precipitation")
def getPrecipitation():
    session = init()
    prcp_df = pd.read_sql(session.query(Measurement.date, Measurement.prcp).statement, session.bind)\
                .set_index('date')\
                    .dropna()\
                        .sort_index()
    prcp_dict = prcp_df.to_dict("dict")['prcp'] 
    return jsonify(prcp_dict)

@app.route("/api/v1.0/stations")
def getStations():
    session = init()
    station_df = pd.read_sql(session.query(Station).statement, session.bind)\
                .set_index('id')\
                    .dropna()\
                        .sort_index()
    station_dict = station_df.to_dict('index')
    return jsonify(station_dict)

@app.route("/api/v1.0/tobs")
def getTobs():
    session = init()
    tobs_df = pd.read_sql(session.query(Measurement.tobs).filter(Measurement.station == most_active, Measurement.date >= past).statement, session.bind)
    tobs_dict = tobs_df.to_dict('list')
    return jsonify(tobs_dict)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def getRange(start=None, end=None):
    session = init()
    if not start:
        start = past
    if not end:
        end = last_date
    range_results = session.query(func.min(Measurement.tobs),\
     func.max(Measurement.tobs),\
          func.avg(Measurement.tobs))\
              .filter(Measurement.station == most_active,\
                  Measurement.date >= start,\
                      Measurement.date <= end)\
                  .first()
    range_dict = {
        'TMIN' : range_results[0],
        'TMAX' : range_results[1],
        'TAVG' : range_results[2]
    }
    return jsonify(range_dict)
