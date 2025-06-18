from flask import Flask,request,jsonify
from dateutil import parser
from threading import Thread
import time
from datetime import datetime,timezone
import requests
app = Flask(__name__)
heartbeats={}
token_map={}
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
@app.route("/")
def hello_world():
    return "<p>I am a rasPi doctor! Nice to meet you</p>"
@app.route("/listener",methods=['POST'])
def listener():
    data=request.get_json()
    device_id=data.get('device_id')
    timestamp=parser.isoparse(data.get('timestamp'))
    last_hb=heartbeats.get(device_id)
    if last_hb and (timestamp-last_hb).total_seconds()>15:
            deathcry(device_id)
    else:
        print("first hearttbeat received from ", device_id)
    heartbeats[device_id]=timestamp
    return jsonify({'status':"Client alive"}),200
def monitor():
    while True:
        for key in list(heartbeats):
            now=parser.isoparse(datetime.now(timezone.utc).isoformat())
            lhb_check=heartbeats.get(key)
            if now-lhb_check>15:
                deathcry(key)

        time.sleep(10)

@app.route("/add_token",methods=['POST'])
def add_token():
    data=request.get_json()
    device_id=data.get('device_id')
    token=data.get('token')
    token_map[device_id]=token
    return jsonify({'status':'token added succesfully'}),200
def deathcry(device_id):
    print("no heartbeat in ",device_id, "for over 30 seconds")
    expo_token=token_map.get(device_id)
    if not expo_token:
        print("not token found for this device",device_id)
        return
    payload={
        "to":expo_token,
        "sound":"default",
        "title":"Server Alert",
        "body":"Alert: Raspi has likely stopped!!!"
    }
    headers={
        "Accept" : "application/json",
        "Accept-Encoding": "gzip,deflate",
        "Content-type": "application/json"
    }
    response=requests.post(EXPO_PUSH_URL,json=payload,headers=headers)
    if (response.status_code != 200):
        return jsonify({"error": "failed to send notification","details": response.text}),500
    heartbeats.pop(device_id)
    print("deathcry sent for ", response)
    return jsonify({"success": True, "expo_response": response.json()})
if __name__ == "__main__":
    Thread(target=monitor,daemon=True).start()
    app.run(host="0.0.0.0", port=5000,debug=False)
    