import logging
import json, os
import nmap3
import time
nmap = nmap3.Nmap()


from flask import request, Response, render_template, jsonify, Flask, current_app
from pywebpush import webpush, WebPushException
results = nmap.scan_top_ports("192.168.0.1/23", args="-sT")
del results['runtime'] 
del results['stats'] 
hosts=results.keys()
print(hosts)
app = Flask(__name__)
app.config['SECRET_KEY'] = '___Add YOUR KEY___'

DER_BASE64_ENCODED_PRIVATE_KEY_FILE_PATH = os.path.join(os.getcwd(),"private_key.txt")
DER_BASE64_ENCODED_PUBLIC_KEY_FILE_PATH = os.path.join(os.getcwd(),"public_key.txt")

VAPID_PRIVATE_KEY = open(DER_BASE64_ENCODED_PRIVATE_KEY_FILE_PATH, "r+").readline().strip("\n")
VAPID_PUBLIC_KEY = open(DER_BASE64_ENCODED_PUBLIC_KEY_FILE_PATH, "r+").read().strip("\n")

VAPID_CLAIMS = {
"sub": "mailto:vraj.vup@gmail.com"
}

def send_web_push(subscription_information, message_body):
    return webpush(
        subscription_info=subscription_information,
        data=message_body,
        vapid_private_key=VAPID_PRIVATE_KEY,
        vapid_claims=VAPID_CLAIMS
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sw.js', methods=['GET'])
def sw():
    return current_app.send_static_file('sw.js')
    
@app.route("/subscription/", methods=["GET", "POST"])
def subscription():
    """
        POST creates a subscription
        GET returns vapid public key which clients uses to send around push notification
    """

    if request.method == "GET":
        return Response(response=json.dumps({"public_key": VAPID_PUBLIC_KEY}),
            headers={"Access-Control-Allow-Origin": "*"}, content_type="application/json")

    subscription_token = request.get_json("subscription_token")
    return Response(status=201, mimetype="application/json")

@app.route("/push_v1/",methods=['POST'])
def push_v1(message):
    
    #print("is_json",request.is_json)

    if not request.json or not request.json.get('sub_token'):
        return jsonify({'failed':1})

    #print("request.json",request.json)

    token = request.json.get('sub_token')
    try:
        token = json.loads(token)
        send_web_push(token, message)
        return jsonify({'success':1})
    except Exception as e:
        print("error",e)
        return jsonify({'failed':str(e)})
@app.route("/scan/",methods=['POST'])
def scan():
	global hosts
	k=0
	while k < 1:
		print("running")
		result = nmap.scan_top_ports("192.168.0.1/23", args="-sT")
		del result['runtime'] 
		del result['stats'] 
		hostsupdates=result.keys()
		print(hostsupdates)
		for i in hostsupdates:
			if i not in hosts:
				message=str(i)+" just connected to network"
				print(message)
				push_v1(message)
		for j in hosts:
			if j not in hostsupdates:
				message=str(j)+" just disconnected from network"
				print(message)
				push_v1(message)
		hosts=hostsupdates
		time.sleep(60)

		
	pass
if __name__ == "__main__":
    app.run(ssl_context=('cert.pem', 'key.pem'),debug=True,host='192.168.1.225')
