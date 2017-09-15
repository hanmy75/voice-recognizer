import time
import signal
import peewee
import datetime
from peewee import *
from miranda import upnp
import xml.etree.ElementTree as ET
from contextlib import contextmanager


WEMO_SERVCE_IP = "192.168.2.12:"

wemos = [
(WEMO_SERVCE_IP + "52000", "TV"),
(WEMO_SERVCE_IP + "52001", "Speaker"),
(WEMO_SERVCE_IP + "52002", "Table"),
(WEMO_SERVCE_IP + "52003", "Center"),
(WEMO_SERVCE_IP + "52004", "Window"),
(WEMO_SERVCE_IP + "52005", "Trick"),
(WEMO_SERVCE_IP + "52006", "Volume"),
(WEMO_SERVCE_IP + "52007", "Stop"),
]

class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException ("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


##################
# Objects/Classes
##################
class wemo_device():
    def __init__(self, ip, shortname):
        self.ip_address = ip
        self.shortname = shortname
        self.timeout_val = 5
        #self.update() #don't want to update at creation time because database may not exist yet on first execution

    def update(self,current_state="ABC123",read=0):
        #collects current state
        if current_state == "ABC123":
            conn = upnp()
            try:
                with time_limit(self.timeout_val):
                    resp = conn.sendSOAP(str(self.ip_address), 'urn:Belkin:service:basicevent:1','http://'+ str(self.ip_address) + '/upnp/control/basicevent1', 'GetBinaryState', {})
                tree = ET.fromstring(resp)    
                current_state = tree.find('.//BinaryState').text
                if str(current_state) != "1" and str(current_state) != "0": current_state = "2"
            except:
                print ("ERROR: Update: Timed out!")
                current_state = "2"

        return current_state

    def on(self,):
        #collects current state
        current_state = self.update()
        #if needed, change state to on
        if current_state == "0" or current_state == "2":
            conn = upnp()
            try:
                with time_limit(self.timeout_val):
                    resp = conn.sendSOAP(str(self.ip_address), 'urn:Belkin:service:basicevent:1', 'http://' + str(self.ip_address) + '/upnp/control/basicevent1', 'SetBinaryState', {'BinaryState': (1, 'Boolean')})
                #new state is returned in the response...checks current state again to confirm success
                tree = ET.fromstring(resp)    
                new_state = tree.find('.//BinaryState').text
                if new_state != "1" and new_state != "0": new_state = "2"
            except:
                print ("ERROR: ON Operation: Timed out!")
                new_state = "2"
            self.update(new_state)
        
            #confirm state change
            if new_state == "1": return "1"
            else: return "0"
        #returns success or failure
        elif current_state=="1": return "1"
        else: return "0"


    def off(self,):
        #collects current state
        current_state = self.update()
        #if needed, change state to off
        if current_state == "1" or current_state == "2":
            conn = upnp()
            try:
                with time_limit(self.timeout_val):
                    resp = conn.sendSOAP(str(self.ip_address), 'urn:Belkin:service:basicevent:1', 'http://' + str(self.ip_address) + '/upnp/control/basicevent1', 'SetBinaryState', {'BinaryState': (0, 'Boolean')})
                #new state is returned in the response...checks current state again to confirm success
                tree = ET.fromstring(resp)    
                new_state = tree.find('.//BinaryState').text
                if new_state != "1" and new_state != "0": new_state = "2"
            except:
                print ("ERROR: OFF Operation: Timed out!")
                new_state = "2"
            self.update(new_state)

            #confirm state change
            if new_state == "0": return "1"
            else: return "0"
        #returns success or failure
        elif current_state=="0": return "1"
        else: return "0"


wemo_dict = {}
for wemo in wemos:
    #print "    creating wemo entry for: " + str(wemo[1])
    wemo_dict[wemo[1]] = wemo_device(wemo[0], wemo[1])
