import json
import logging

def findDictInList(list, key, value):
    retVal = None
    for listDict in list:
        if listDict.get(key) == value:
            return listDict
    return None
         
def sendInt2Domoticz(client, topic, idx, value):
    jsonString = '{ "idx" : %s, "nvalue" : %d, "svalue" : "" }' % (idx, value)
    logging.debug("Sending to domo: %s", jsonString)
    client.publish(client, topic, payload = jsonString)
	
def sendString2Domoticz(client,topic,  idx, value):
    jsonString = '{ "idx" : %s, "nvalue" : 0, "svalue" : "%s" }'  % (idx, value)
    logging.debug("Sending to domo: %s", jsonString)
    client.publish(topic, payload = jsonString)
	

class Inverter:
    def __init__(self, inverter, inverterConfig,logging, topicDomoticz):
        self.inverter = inverter
        self.logging = logging
        self.topicDomoticz = topicDomoticz
        self.keyItems = []
        for key in inverterConfig:
           idx = int(inverterConfig[key])
           self.keyItems.append( { "key" : key, "idx" : idx} )
        self.logging.debug("items: %s", self.keyItems) 

    def processOnline(self, parsedJson, client):
        keyDict = findDictInList(self.keyItems, "key", "online")
        if keyDict == None:
            self.logging.warning("online not defined for inverter. skipping")
            return
        idx = keyDict["idx"]
        if idx == None:
            self.logging.warning("Program Error: no value found for idx of inverter")

        numericValue =  parsedJson

        self.logging.debug("numeric value for online: %s", numericValue)
        if numericValue == 0:
            value = "Offline"
        else: 
            value = "Online"
        self.logging.debug("Online = %s", value)
        sendString2Domoticz(client, self.topicDomoticz, idx, value)

    def processData(self, parsedJson, client):
        self.logging.debug("Processing data message %s", parsedJson)
        invertype = parsedJson["inverterType"]
        runningInfo = parsedJson["runningInfo"]
        for keyDict in self.keyItems:
            key = keyDict["key"]
            idx = keyDict["idx"]


            # TODO: fix 3 phase inverters
            if key == "online":
                # nothing to do
                dummy = key
            elif key   == "power_daytotal":
                dayTotal = runningInfo["eDay"]
                dayTotalWh = float(dayTotal) * 1000
                value = "%.1f" % dayTotalWh
                sendString2Domoticz(client, self.topicDomoticz, idx, value)
            elif key == "power_grand_total":
                value = runningInfo["eTotal"]
                sendString2Domoticz(client, self.topicDomoticz, idx, value)
            elif key == "errormessage":
                value = runningInfo["errorMessage"]
                self.logging.debug("Errormessage = %s", value)
                if not value:
                    value = "None"
                sendString2Domoticz(client, self.topicDomoticz, idx, value)
            elif key == "mains_frequency":
                value = runningInfo["fac1"]
                sendString2Domoticz(client, self.topicDomoticz, idx, value)
            elif key == "total_hours":
                value = runningInfo["hTotal"]
                sendString2Domoticz(client, self.topicDomoticz, idx, value)
            elif key == "mains_current":
                value = runningInfo["iac1"]
                sendString2Domoticz(client, self.topicDomoticz, idx, value)
            elif key == "input1_current":
                value = runningInfo["ipv1"]
                sendString2Domoticz(client, self.topicDomoticz, idx, value)
            elif key == "input2_current":
                value = runningInfo["ipv2"]
                sendString2Domoticz(client, self.topicDomoticz, idx, value)
            elif key == "current_power":
                pac = runningInfo["pac"]
                dayTotal = runningInfo["eDay"]
                dayTotalWh = float(dayTotal) * 1000
                value = "%s;%.1f" % (pac, dayTotalWh)
                sendString2Domoticz(client, self.topicDomoticz, idx, value)
            elif key == "temperature":
                value = runningInfo["temp"]
                sendString2Domoticz(client, self.topicDomoticz, idx, value)
            elif key == "mains_voltage":
                value = runningInfo["vac1"]
                sendString2Domoticz(client, self.topicDomoticz, idx, value)
            elif key == "input1_voltage":
                value = runningInfo["vpv1"]
                sendString2Domoticz(client, self.topicDomoticz, idx, value)
            elif key == "input2_voltage":
                value = runningInfo["vpv2"]
                sendString2Domoticz(client, self.topicDomoticz, idx, value)
            else:
                self.logging.warning("Found unknown key %s for inverter %s", key, self.inverter)



class Json2Domo:

    def __init__(self, logging, topicGoodwe, topicDomoticz):
        self.logging = logging
        self.inverters = []
        self.topicGoodwe = topicGoodwe
        self.topicDomoticz = topicDomoticz

    def addInverter(self, inverter, config):
        self.logging.debug("Json2Domo: Adding inverter %s", inverter)
        if not inverter in config:
            self.logging.error("Configuration for inverter %s not found in configuration file, skipping!!!", inverter)
            return

        # TODO check if inverter already in list

        inverterConfig = config[inverter]
        mapper = Inverter(inverter, inverterConfig, self.logging, self.topicDomoticz)
        self.inverters.append( { "inverter" : inverter, "mapper" : mapper })
        self.logging.debug("Inverter list = %s", self.inverters)

    def goodWeMessage(self, message, client):
        self.logging.debug("Received message on topic %s" , (message.topic))
        goodweJson = json.loads(message.payload)

        path = []
        for component in message.topic.split('/'):
            path.append(component.strip())
        self.logging.debug("Message path = %s", path)

        if path[0] == self.topicGoodwe:
            inverter = path[1]
            dictObject = findDictInList(self.inverters, "inverter", inverter)
            if dictObject == None:
                self.logging.debug("Inverter %s is not defined, skipping message", path[2])
                return
           
            mapper = dictObject["mapper"]
            if path[2] == "data":
                mapper.processData(goodweJson, client)
            elif path[2] == "online":
                mapper.processOnline(goodweJson, client)
            else:
                self.logging.debug("Unknown message type: %s", path[3])
        else:
            self.logging.debug("Incorrect topic %s (expected %s)in message, skipping", path[0], self.topicGoodwe)
