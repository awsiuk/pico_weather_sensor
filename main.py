import network
import socket
import time
import machine
from myENS160 import *
from myVEML7700 import *
#from myAHT20 import *
from BME280 import *
from config import *

data={
    "temp": 0.0,
    "hum": 0.0,
    "AQI": 0,
    "TVOC": 0,
    "eCO2": 0,
    "lux": 0,
    "pressure": 0.0}

def open_socket(ip):
    # Open a socket
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    print(connection)

def create_json_view():
    html_view="""{ "temp": %s, "hum": %s, "AQI": %s, "TVOC": %s, "eCO2": %s, "lux": %s, "pressure": %s }"""%(data["temp"],data["hum"],data["AQI"],data["TVOC"],data["eCO2"],data["lux"],data["pressure"])
    return html_view
    
    
def create_user_view():
#AQI levels
#very good: 0-20
#good: 20.1 - 50
#moderate: 50.1 - 80
#fair: 80.1 - 110
#bad: 110.1 - 150
#very bad: >150
#
    _aqi=data["AQI"]
    
    if _aqi<=20:
        AQI_COLOR="#66cc00"
    elif _aqi<=50:
        AQI_COLOR="#00cc00"
    elif _aqi<=80:
        AQI_COLOR="#f4dd2d"
    elif _aqi<=110:
        AQI_COLOR="#f98c1f"
    elif _aqi<=150:
        AQI_COLOR="#f91f1f"
    else:
        AQI_COLOR="#ae2f04"

    
    return html_view

def get_data():
    data["AQI"]=ens.getAQI()
    data["TVOC"]=ens.getTVOC()
    data["eCO2"]=ens.getECO2()    
    data["lux"]=round(VEML.getLuxAls(),1)
    #Wdata=aht.getWeather()
    data["temp"]=round(bme.temperature,1)+temp_corr
    data["hum"]=round(bme.humidity,1)+hum_corr
    data["pressure"]=bme.pressure

def html_err_msg(code):
    if code==400:
        err_description="Unsupported syntax"
    err_file=open("errPage.html","r")
    err_content=err_file.read()
    err_file.close()
    error_header="HTTP/1.0 "+str(code)+" "+err_description+"\r\nServer: lightLATECH\r\nContent-Type: text/html;charset=utf-8\r\nContent-Length: "
    error_message=error_header+str(len(err_content))+"\r\n\r\n"+err_content
    return error_message

def process_req(buffer):
    try:
        url=(str(buffer).split())[1].lower()
    except:
        url="GET /"
    
    uri=(str(url).split)[1].lower()
    
            
    if url == "/view":
        html=create_user_view()
    else:
        html=create_json_view()

def new_request(buf):
    #connection needs to be closed by client not by server.
    #grab data from buffer
    try:
        print(buf)
        url=(buf.split())[1]
        method=((buf.split())[0]).split("'")[1]
    except:
        client.send(html_err_msg(400))
        return
    
    if method.upper() != "GET":
        client.send(html_err_msg(400))
        return
    
    
    print("processing url:",url)
    if url=="/" or url.lower()=="/index.html":
        index_file="index.html"
        client.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        f=open(index_file,"r")
        #we need to read it and test out parsing
        html_main=str(f.read()).format(nodename,data["temp"], data["hum"], data["AQI"], data["TVOC"], data["eCO2"],data["lux"])
        
        client.send(html_main)
        f.close()
    elif url=="/api":
        client.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        client.send(create_json_view())
    else:
        url=url[1:]
        try:
            ext=url.split(".")[1].lower()
        except:
            ext=""
        if not(ext=="html" or ext=="jpg" or ext=="jpeg" or ext=="png" or ext=="gif" or ext=="css" or ext=="ico"):
            client.send(html_err_msg(400))
        else:
            
            if ext=="css":
                content_type="text/css"
            elif ext=="jpg" or ext=="jpeg":
                content_type="image/jpeg"
            elif ext=="gif":
                content_type="image/gif"
            elif ext=="png":
                content_type="image/png"
            elif ext=="ico":
                content_type="image/x-icon"
            else:
                content_type="text/html"
            
            try:
                f=open(url,"rb")
                client.send('HTTP/1.0 200 OK\r\nContent-type: '+content_type+'\r\n\r\n')
                client.send(f.read())
                f.close()
            except:
                client.send(html_err_msg(400))
                


    
SCL_PIN=machine.Pin(1)
SDA_PIN=machine.Pin(0)
i2c=machine.I2C(0,scl=SCL_PIN, sda=SDA_PIN,freq=400000)

VEML=myVEML7700(i2c)
ens=myENS160(i2c)
#aht=myAHT20(i2c)
bme=BME280(i2c=i2c)
VEML.setGain(VEML7700_ALS_GAIN_1_8)
VEML.setALS(VEML7700_ALS_100MS)

get_data()
time.sleep(5)

SSID = "la-tech-2g"
PASSWORD = "dione2008###.,"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)
while wlan.isconnected() == False:
    print('Waiting for WiFi connection...')
    time.sleep(1)
ip = wlan.ifconfig()[0]
print(f'Wifi connected on {ip}')

address = (ip, 80)
connection = socket.socket()
connection.bind(address)
connection.listen(1)
print(connection)

while True:
        print("Web server is waiting for connection")
        client, client_addr = connection.accept()
        print("Incoming connection from:", str(client_addr))
        request = client.recv(2048)
        request = str(request)
        get_data()
        new_request(request)

        client.close()