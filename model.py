from flask import Flask,jsonify,request,render_template
import pandas as pd
import numpy as np
from math import sin, cos, sqrt, atan2, radians
import requests
import nltk
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('Website.html')

@app.route('/', methods=['POST'])
def do():
    a1 = request.form['city']  # Get the city input from the form
    a2 = request.form['add']
    a3 = request.form['nec']
    a4 = request.form['g']
    address = a2
    city = a1
    print(a4)
    if a4 == '':
        number = 4
    else:
        number = int(a4)
    features = a3
    if a3 == '':
        features = ''
    R = 6373.0  # Earth's Radius
    api = '4519d076b432f5'
    current_dir = os.path.dirname(os.path.abspath(__file__))

# Read Hotel_details.csv using a relative path
    csv_file_path = os.path.join(current_dir, 'Hotel_details.csv')
    hotel_details = pd.read_csv(csv_file_path, delimiter=',')

# Read Hotel_Room_attributes.csv using an absolute path
    room_attributes_file_path = os.path.join(current_dir, 'Hotel_Room_attributes.csv')
    hotel_rooms = pd.read_csv(room_attributes_file_path, delimiter=',')

# Read hotels_RoomPrice.csv using an absolute path
    cost_file_path = os.path.join(current_dir, 'hotels_RoomPrice.csv')
    hotel_cost = pd.read_csv(cost_file_path, delimiter=',')
    del hotel_details['id']
    del hotel_rooms['id']
    del hotel_details['zipcode']
    hotel_details=hotel_details.dropna()
    hotel_rooms=hotel_rooms.dropna()
    hotel_details.drop_duplicates(subset='hotelid',keep=False,inplace=True)
    hotel=pd.merge(hotel_rooms,hotel_details,left_on='hotelcode',right_on='hotelid',how='inner')
    optimum_band_file_path = os.path.join(current_dir, 'hotel_price_min_max - Formula.csv')
    optimum_band = pd.read_csv(optimum_band_file_path, delimiter=',')
    del hotel['hotelid']
    del hotel['url']
    del hotel['curr']
    del hotel['Source']
    sw = stopwords.words('english')
    lemm = WordNetLemmatizer()
    url = "https://us1.locationiq.com/v1/search.php"
    hotel['roomamenities']=hotel['roomamenities'].str.replace(': ;',',')
    features_tokens=word_tokenize(features)
    f1_set = {w for w in features_tokens if not w in sw}
    f_set=set()
    for se in f1_set:
        f_set.add(lemm.lemmatize(se))
    data = {
    'key': api,
    'q': address,
    'format': 'json'}
    response = requests.get(url, params=data)
    dist=[]
    lat1,long1=response.json()[0]['lat'],response.json()[0]['lon']
    lat1=radians(float(lat1))
    long1=radians(float(long1))
    hybridbase = hotel
    hybridbase['city'] = hybridbase['city'].str.lower()
    hybridbase = hybridbase[hybridbase['city'] == city.lower()]  # Filter by the user's specified city
    hybridbase.drop_duplicates(subset='hotelcode', inplace=True, keep='first')
    # Rest of your code...

    hybridbase=hybridbase.set_index(np.arange(hybridbase.shape[0]))
    for i in range(hybridbase.shape[0]):
        lat2=radians(hybridbase['latitude'][i])
        long2=radians(hybridbase['longitude'][i])
        dlon = long2 - long1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c
        dist.append(distance)
    hybridbase['distance']=dist
    hybridbase=hybridbase[hybridbase['distance']<=5]
    hybridbase=hybridbase.set_index(np.arange(hybridbase.shape[0]))
    coss=[]
    for i in range(hybridbase.shape[0]):
        temp_tokens=word_tokenize(hybridbase['roomamenities'][i])
        temp1_set={w for w in temp_tokens if not w in sw}
        temp_set=set()
        for se in temp1_set:
            temp_set.add(lemm.lemmatize(se))
        rvector = temp_set.intersection(f_set)
        coss.append(len(rvector))
    hybridbase['similarity']=coss
    h=hybridbase.sort_values(by='similarity',ascending=False)
    price_band=pd.merge(h,optimum_band,left_on=['hotelcode'],right_on=['hotelcode'],how='inner')
    price_band=pd.merge(price_band,hotel_cost,left_on=['hotelcode'],right_on=['hotelcode'],how='inner')
    del price_band['min']
    del price_band['max']
    del price_band['Diff_Min']
    del price_band['Diff_Max']
    del price_band['currency']
    del price_band['country']
    del price_band['propertytype']
    del price_band['starrating']
    del price_band['latitude']
    del price_band['longitude']
    price_band=price_band[price_band['Score']<=0.5]
    price_band=price_band[price_band['maxoccupancy']>=number]
    price_band.drop_duplicates(subset='hotelcode',inplace=True,keep='first')
  # Generate the HTML table
    # Generate the HTML table
    d1 = price_band[['hotelname', 'distance', 'roomtype_x', 'address', 'city', 'onsiterate', 'maxoccupancy']].head(5)
    html_table = d1.to_html(index=False, escape=False)

    # Add Bootstrap CDN link, apply Bootstrap classes, set background image without transparency, and add heading and button
    html = f'''
    <html>
    <head>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            body {{
                background-image: url('https://images.pexels.com/photos/1268871/pexels-photo-1268871.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1');
                background-repeat: no-repeat;
                background-size: cover;
                background-attachment: fixed;
            }}
            .container {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }}
            .table {{
                background-color: rgba(255, 255, 255, 1);
            }}
            .table thead {{
                background-color: #000; /* Black background for the table header */
                color: #fff; /* White text color for the table header */
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Recommended Hotels</h1>
             <table class="table table-bordered table-striped table-hover> 
            {html_table}
            <button class="btn btn-primary" onclick="location.href='/'">Try Another?</button>
        </div>
    </body>
    </html>
    '''

    # Save the modified HTML to the ind.html file
    with open("templates/ind.html", "w") as text_file:
        text_file.write(html)

    return render_template("ind.html")

if __name__ == '__main__':
    app.run(debug=True)






