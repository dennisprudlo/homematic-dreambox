### Header ###################################
# -*- coding: utf-8 -*-


### Imports ##################################

# urllib/2, um die XML Files zu laden
import urllib2
import httplib
from xml.dom import minidom

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox

from Components.Label import Label
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Input import Input

from skin import parseColor

from Plugins.Plugin import PluginDescriptor

################################################

class DeviceScreen(Screen):

    # channel information
    channelList = []
    stateXML = []
    # lists
    device_list = 'http://192.168.178.43/addons/xmlapi/devicelist.cgi'
    state_list = 'http://192.168.178.43/addons/xmlapi/statelist.cgi'
    state_change = '/addons/xmlapi/statechange.cgi'

    skin = """
        <screen position="100,100" size="1100,540" title="HomematicTV 0.8" >
            <widget name="menuFunctions" position="10,20" size="420,500" scrollbarMode="showOnDemand" />

            <widget name="labelSelection" position="450,20" size="600,40" font="Regular;35" />
            <widget name="labelInfoConst" position="450,70" size="300,100" font="Regular;20" />
            <widget name="labelInfoValue" position="770,70" size="620,100" font="Regular;20" />

            <widget name="labelStatus" position="1000,-130" size="55,200" font="Regular;200" />

            <widget name="labelWeatherInfo" position="450,180" size="600,40" font="Regular;35" />
            <widget name="labelDataConst" position="450,230" size="300,300" font="Regular;20" />
            <widget name="labelDataValue" position="770,230" size="620,300" font="Regular;20" />

            <widget name="functionRed" position="450,485" size="150,35" backgroundColor="#11440000" valign="center" halign="center" zPosition="2" foregroundColor="white" font="Regular;20"/>
            <widget name="functionGreen" position="610,485" size="150,35" backgroundColor="#11004400" valign="center" halign="center" zPosition="2" foregroundColor="white" font="Regular;20"/>
            <widget name="functionYellow" position="770,485" size="150,35" backgroundColor="#11444400" valign="center" halign="center" zPosition="2" foregroundColor="white" font="Regular;20"/>
            <widget name="functionBlue" position="930,485" size="150,35" backgroundColor="#11000044" valign="center" halign="center" zPosition="2" foregroundColor="white" font="Regular;20"/>
        </screen>
    """

    def __init__(self, session, args = None):
        print "  -- [HomematicTV] --  class DeviceScreen(Screen):initialize"
        self.session = session

        ## download state channel
        self.downloadStateXml()
        self.channelList = []

        self.downloadXml(self.device_list, "_devices")

        menuMain = []
        for item in self.channelList:
            menuMain.append((_(str(item[3][:-2].encode('utf-8'))), item[0]))

        # Event Manager
        Screen.__init__(self, session)
        self["menuFunctions"] = MenuList(menuMain)

        self["labelSelection"] = Label()
        self["labelInfoConst"] = Label(_("Gerätetyp:\nRichtung:"))
        self["labelInfoValue"] = Label()

        self["labelStatus"] = Label(_("."))

        self["labelWeatherInfo"] = Label(_("Wetter"))
        self["labelDataConst"] = Label(_(" "))
        self["labelDataValue"] = Label(_(" "))

        # show weather information
        self.setDataInformation("2442", "Wetterstation") # weather station ise_id, type


        self["functionRed"] =       Label(_(" "))
        self["functionGreen"] =     Label(_("Einschalten"))
        self["functionYellow"] =    Label(_("Ausschalten"))
        self["functionBlue"] =      Label(_("Dimmen"))

        self["myActionMap"] = ActionMap(["SetupActions", "ColorActions", "InfobarChannelSelection"],
        {
            "ok":           self.clickOk,
            "cancel":       self.clickExit,
            "switchChannelUp":           self.clickUp,
            "switchChannelDown":         self.clickDown,
                #"red":      self.clickRed,
                "green":    self.clickGreen,
                "yellow":   self.clickYellow,
                "blue":     self.clickBlue
        }, -1)
        self.onShown.append(self.updateSelection)

    ### Events ###################################
    def clickOk(self):
        self.updateSelection()

    def clickExit(self):
        self.close(None)

    def clickUp(self):
        self["menuFunctions"].up()
        self.updateSelection()

    def clickDown(self):
        self["menuFunctions"].down()
        self.updateSelection()

    def clickRed(self):
        self.messageBox("Red", MessageBox.TYPE_INFO)

    def clickGreen(self):
        httpServ = httplib.HTTPConnection("192.168.178.43", 80)
        httpServ.connect()

        ise_id = str(self.getSelectedItemArray()[0])
        name = str(self.getSelectedItemArray()[3])
        type_num = str(self.getSelectedItemArray()[2])
        type = self.getChannelType(str(type_num))

        if type == "Funk-Schaltaktor":
            httpServ.request('GET', "{}?ise_id={}&new_value=true".format(self.state_change, ise_id))
        elif type == "Funk-Dimmaktor" or type == "Funk-Rolladenaktor":
            if type == "Funk-Dimmaktor" or type == "Funk-Rolladenaktor" and name.startswith("Markise"):
                httpServ.request('GET', "{}?ise_id={}&new_value=1.0".format(self.state_change, ise_id))
            else:
                httpServ.request('GET', "{}?ise_id={}&new_value=0.0".format(self.state_change, ise_id))

        self.updateStateStatus(ise_id, 1)
        self.updateSelection()


    def clickYellow(self):
        httpServ = httplib.HTTPConnection("192.168.178.43", 80)
        httpServ.connect()

        ise_id = str(self.getSelectedItemArray()[0])
        name = str(self.getSelectedItemArray()[3])
        type_num = str(self.getSelectedItemArray()[2])
        type = self.getChannelType(str(type_num))

        if type == "Funk-Schaltaktor":
            httpServ.request('GET', "{}?ise_id={}&new_value=false".format(self.state_change, ise_id))
        elif type == "Funk-Dimmaktor" or type == "Funk-Rolladenaktor":
            if type == "Funk-Dimmaktor" or type == "Funk-Rolladenaktor" and name.startswith("Markise"):
                httpServ.request('GET', "{}?ise_id={}&new_value=0.0".format(self.state_change, ise_id))
            else:
                httpServ.request('GET', "{}?ise_id={}&new_value=1.0".format(self.state_change, ise_id))

        self.updateStateStatus(ise_id, 0)
        self.updateSelection()

    def clickBlue(self):
        type_num = str(self.getSelectedItemArray()[2])
        type = self.getChannelType(str(type_num))

        if type == "Funk-Dimmaktor" or type == "Funk-Rolladenaktor":
            if type == "Funk-Dimmaktor":
                lblHead = "Dimmen"
                lblTitle = "Gebe den Helligkeitswert in Prozent ein:"
            elif type == "Funk-Rolladenaktor":
                lblHead = "Rolladen ausfahren"
                lblTitle = "Gebe eine Position für die Rolladen in Prozent an:"
            self.session.openWithCallback(self.inputDimmingValue, InputBox, title=lblTitle, windowTitle=lblHead, text=" " * 30, maxSize=40, type=Input.NUMBER)
    ### Events ###################################


    ### Functions #################################
    def downloadStateXml(self):
        # download xml file
        response = urllib2.urlopen(self.state_list)
        file_xml = open("tmpState.xml", "w")
        file_xml.write(response.read())
        file_xml.close()
        self.stateXML = minidom.parse("tmpState.xml")

    def inputDimmingValue(self, word):
        if word is None:
            pass
        else:
            httpServ = httplib.HTTPConnection("192.168.178.43", 80)
            httpServ.connect()

            send = str(float(word) / 100.0)

            ise_id = str(self.getSelectedItemArray()[0])
            type_num = str(self.getSelectedItemArray()[2])

            httpServ.request('GET', "{}?ise_id={}&new_value={}".format(self.state_change, ise_id, send))

            if type_num == "27" or type_num == "36":
                if float(word) > 0:
                    self.updateStateStatus(ise_id, 1)
                else:
                    self.updateStateStatus(ise_id, 0)

            self.updateSelection()

    def updateSelection(self):
        name = str(self.getSelectedItemArray()[3][:-2])
        ise_id = str(self.getSelectedItemArray()[0])
        type_num = str(self.getSelectedItemArray()[2])
        stateOn = self.getSelectedItemArray()[6]

        type = self.getChannelType(str(type_num))
        direction = self.getChannelDirection(str(self.getSelectedItemArray()[4]))

        self["labelSelection"].setText(name)

        self.setSpecInfo(ise_id, type, direction)

        if stateOn == 1:
            self["labelStatus"].instance.setForegroundColor(parseColor("#11004400"))    #aarrggbb
        else:
            self["labelStatus"].instance.setForegroundColor(parseColor("#11440000"))    #aarrggbb

        self["labelStatus"].instance.invalidate()

        self.updateButtonText(type, name)

    def setDataInformation(self, ise_id, type):
        channel_nodes = self.stateXML.getElementsByTagName('channel')
        for channel in channel_nodes:
            if channel.getAttribute('ise_id') == str(ise_id):
                datapoint_nodes = channel.getElementsByTagName('datapoint')
                if type == "Wetterstation":
                    self.setData_Weatherstation(datapoint_nodes)

    def setData_Weatherstation(self, datapoint_list):
        self["labelDataConst"].setText("Temperatur:\nLuftfeuchtigkeit:\nRegen:\nWindgeschwindigkeit:\nWindrichtung:\nWindr. Schwankungsbreite:\nSonnenscheindauer:\nHelligkeit:\nRegenmenge heute:\nRegenmenge gestern:")

        text = "{} °C\n{}%\n{}\n{} km/h\n{}°\n{}°\n{}\n{}\n{} mm\n{} mm".format(
            round(float(datapoint_list[0].getAttribute('value')), 2),
            datapoint_list[1].getAttribute('value'),
            self.boolToPseudo(datapoint_list[2].getAttribute('value')),
            round(float(datapoint_list[4].getAttribute('value')), 2),
            self.degreesToDirection(datapoint_list[5].getAttribute('value')),
            datapoint_list[6].getAttribute('value'),
            datapoint_list[7].getAttribute('value'),
            datapoint_list[8].getAttribute('value'),
            round(float(datapoint_list[9].getAttribute('value')), 2),
            round(float(datapoint_list[10].getAttribute('value')), 2)
        )
        self["labelDataValue"].setText(text)

    def setSpecInfo(self, ise_id, type, direction):

        valname = "Status"
        valtype = "STATE"
        if type == "Funk-Dimmaktor":
            valtype = "LEVEL"
            valname = "Dimmung"
        elif type == "Funk-Sensor" and ise_id != "1671" and ise_id != "3908":
            valtype = "SET_TEMPERATURE"
            valname = "Temperatur"
        elif type == "Funk-Sensor":
            valtype = "MOTION"
            valname = "Bewegung erkannt"
        elif type == "Funk-Rolladenaktor":
            valtype = "LEVEL"
            valname = "Einstellung"
        elif type == "Funk-Temperaturmesser":
            valtype = "TEMPERATURE"
            valname = "Temperatur"

        self["labelInfoConst"].setText("Gerätetyp:\nRichtung:\n\n{}:".format(valname))

        channel_nodes = self.stateXML.getElementsByTagName('channel')
        for channel in channel_nodes:
            if channel.getAttribute('ise_id') == str(ise_id):
                datapoint_nodes = channel.getElementsByTagName('datapoint')
                for datapoint in datapoint_nodes:
                    if datapoint.getAttribute('type') == valtype:
                        exportVal = datapoint.getAttribute('value')
                        if type == "Funk-Schaltaktor":
                            exportVal = self.boolToPseudo(exportVal, "Eingeschaltet", "Ausgeschaltet")
                        elif type == "Funk-Dimmaktor":
                            exportVal = "{} %".format(round(float(exportVal) * 100, 2))
                        elif type == "Funk-Sensor" and ise_id != "1671" and ise_id != "3908":
                            exportVal = "{} °C".format(round(float(exportVal), 2))
                        elif type == "Funk-Sensor":
                            exportVal = self.boolToPseudo(exportVal)
                        elif type == "Funk-Rolladenaktor":
                            exportVal = "{} %".format(round(float(exportVal) * 100, 2))
                        elif type == "Funk-Temperaturmesser":
                            exportVal = "{} °C".format(round(float(exportVal), 2))

                        self["labelInfoValue"].setText("{}\n{}\n\n{}".format(type, direction, exportVal))



    def boolToPseudo(self, bool, true = "Ja", false = "Nein"):
        if bool == "true":
            return true
        else:
            return false

    def degreesToDirection(self, degrees):
        deg = int(degrees)
        if deg >= 338 or deg <= 22:
            return "N {}".format(degrees)
        if deg >= 23 and deg <= 67:
            return "NO {}".format(degrees)
        if deg >= 68 and deg <= 112:
            return "O {}".format(degrees)
        if deg >= 113 and deg <= 157:
            return "SO {}".format(degrees)
        if deg >= 158 and deg <= 202:
            return "S {}".format(degrees)
        if deg >= 203 and deg <= 247:
            return "SW {}".format(degrees)
        if deg >= 248 and deg <= 292:
            return "W {}".format(degrees)
        if deg >= 293 and deg <= 337:
            return "NW {}".format(degrees)

    def updateButtonText(self, type, name):
        if type == "Funk-Schaltaktor":
            lblGreen = "Einschalten"
            lblYellow = "Ausschalten"
            lblBlue = " "
        elif type == "Funk-Dimmaktor":
            lblGreen = "Einschalten"
            lblYellow = "Ausschalten"
            lblBlue = "Dimmen"
        elif type == "Funk-Rolladenaktor":
            lblGreen = "Ausfahren"
            lblYellow = "Einfahren"
            lblBlue = "Setzen"
        elif type == "Funk-Temperaturmesser" and name != "Wetterstation":
            lblGreen = " "
            lblYellow = " "
            lblBlue = "Setzen"
        elif type == "Funk-Sensor" and name.startswith("Bewegungsmelder") == 0:
            lblGreen = " "
            lblYellow = " "
            lblBlue = "Setzen"
        else:
            lblGreen = " "
            lblYellow = " "
            lblBlue = " "

        self.setFunctionText("functionGreen", lblGreen)
        self.setFunctionText("functionYellow", lblYellow)
        self.setFunctionText("functionBlue", lblBlue)

    def getChannelType(self, type):
        if type == "26":
            return "Funk-Schaltaktor"
        elif type == "17":
            return "Funk-Sensor"
        elif type == "22":
            return "Funk-Temperaturmesser"
        elif type == "27":
            return "Funk-Dimmaktor"
        elif type == "36":
            return "Funk-Rolladenaktor"
        elif type == "37":
            return "Funk- Tür-/Fensterkontakt"
        else:
            return "Unbekannter Typ"

    def getChannelDirection(self, direction):
        if direction == "RECEIVER":
            return "Aktor"
        elif direction == "SENDER":
            return "Sensor"

    def getSelectedItemArray(self):
        retval = self["menuFunctions"].l.getCurrentSelection()[1] #chid
        for idx, itm in enumerate(self.channelList):
            if itm[0] == retval:
                return self.channelList[idx]

    def updateStateStatus(self, ise_id, value):
        for idx, itm in enumerate(self.channelList):
            if itm[0] == ise_id:
                self.channelList[idx][6] = value
                self.updateSelection()


    def setFunctionText(self, function, text):
        self[function].setText(text)

    # download XML file and set channel list
    def downloadXml(self, url, tag):
        # download xml file
        response = urllib2.urlopen(url)
        file_xml = open("%s.xml" % tag, "w")
        file_xml.write(response.read())
        file_xml.close()
        xmltmp = minidom.parse("%s.xml" % tag)
        xmlChannels = xmltmp.getElementsByTagName('channel')
        for ls_ch in xmlChannels:

            name =              ls_ch.getAttribute('name')
            if name.startswith("HM-"):
                continue

            ise_id =            ls_ch.getAttribute('ise_id')
            address =           ls_ch.getAttribute('address')
            type =              ls_ch.getAttribute('type')
            direction =         ls_ch.getAttribute('direction')
            visible =           ls_ch.getAttribute('visible')
            statusState =       self.getStatusState(ise_id, type)
            # add channel to list
            self.channelList.append([ ise_id, address, type, name, direction, visible, statusState ])

    def getStatusState(self, channel_ise, type_num):
        statusStateType = "STATE"
        if type_num == "27":
            statusStateType = "LEVEL"

        xmlChannels = self.stateXML.getElementsByTagName('channel')
        # list channels
        for ch_node in xmlChannels:
            if ch_node.getAttribute('ise_id') == str(channel_ise):
                datapoint_node = ch_node.getElementsByTagName('datapoint')
                for datapoint in datapoint_node:
                    if datapoint.getAttribute('type') == statusStateType:
                        value = datapoint.getAttribute('value')
                        if value == "false":
                            return 0
                        elif type_num == "27" and float(value) <= 0.0:
                            return 0
                        else:
                            return 1
    ### Functions #################################


    def messageBox(self, message, type):
        self.session.open(MessageBox,_(message), type)


###########################################################################

def main(session, **kwargs):
    print "\n  -- [HomematicTV] -- start\n\n"
    session.open(DeviceScreen)

###########################################################################

def Plugins(**kwargs):
    return PluginDescriptor(
        name="HomematicTV",
        description="Homematic Aktorenschalter für enigma2",
        where = PluginDescriptor.WHERE_PLUGINMENU,
        icon="hmdreambox.png",
        fnc=main
    )
