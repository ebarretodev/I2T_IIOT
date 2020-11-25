#coding: utf-8
'''
----------------------------------------------------------
Created:04/10/2020
Author: Eliabel Barreto
Customer: Julio-S4B Tech
Objective: Developed interface OEE system in industry floor
----------------------------------------------------------
'''

#Definição de versão de projeto
__version__ = '1.0'

#############################
#Configuração das bibliotecas
#############################

#configuração da versão do framework kivy
import kivy
kivy.require('1.10.0')

from kivy.app import App
from kivy.uix.screenmanager import Screen,ScreenManager,ShaderTransition
from kivy.properties import StringProperty, ListProperty,NumericProperty, BooleanProperty


#para eventos temporizados
from kivy.clock import Clock
import time
from datetime import datetime

#necessario para usar cores em HEX
from kivy.utils import get_color_from_hex
from kivy.core.window import Window
Window.clearcolor = get_color_from_hex('#FFFFFF')
Window.fullscreen = True
Window.size = (1024,600)

#configurando o teclado virtual
from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemanddock')
Config.set('kivy', 'keyboard_layout', 'qwerty')
Config.write()

#modulo para ler dados do clp
from bin.calculos import Machine
from bin.mqttconn import MQTT_IOTA_STREAMS
import json
#teclados

#############################
#Programação
#############################

#classe de gerenciador de telas
class Gerenciador(ScreenManager):
    pass

#classe de telas a serem usadas

class Startup(Screen):
    #Tela de inicialização, apos 3 segundos inicializa a tela
    def TrocaTela(self, *args):
        App.get_running_app().root.current = 'operacao'

    def on_enter(self, *args):
        Clock.schedule_once(self.TrocaTela, 3)

class Inicio(Screen):

    def ConfigScreen(self):
        App.get_running_app().root.current = 'configuracao'

    def iniciar(self):
        App.get_running_app().root.current = 'operacao'

class Operacao(Screen):
    def finalizar(self):
        App.get_running_app().root.current = 'inicio'




class Configuracao(Screen):

    def voltar(self):
        App.get_running_app().root.current = 'inicio'

#classe do aplicativo
class s4boee(App):
    Robot = Machine(48, 32)
    TangleConn = MQTT_IOTA_STREAMS('RaspberryS4B', 'localhost')
    your_time = StringProperty()
    your_date = StringProperty()
    desempenho_maquina = NumericProperty()
    OEE_Color = ListProperty()
    Availability_Color = ListProperty()
    Performance_Color = ListProperty()
    Quality_Color = ListProperty()
    time = NumericProperty()
    limittime = NumericProperty()
    Register = BooleanProperty()
    Availability = NumericProperty()
    Performance = NumericProperty()
    Quality = NumericProperty()
    OEE = NumericProperty()
    lastOEE = NumericProperty()

    def __init__(self, **kwargs):
        super(s4boee, self).__init__(**kwargs)
        Clock.schedule_interval(self.set_time, 1)
        Clock.schedule_interval(self.atualiza, .05)
        Clock.schedule_interval(self.getValuePLC, 1)
        Clock.schedule_interval(self.getDataStoped, 1)
        Clock.schedule_interval(self.Robot.checkProducing, 1)
        Clock.schedule_interval(self.Robot.checkGoodParts, 1)
        Clock.schedule_interval(self.Robot.CalcIndicators, 1)
        Clock.schedule_interval(self.sendData2Tangle, 1)

    def build(self):
        return Gerenciador(transition=ShaderTransition())

    def getValuePLC(self, dt):
        self.Availability = self.Robot.Availability
        self.Performance = self.Robot.Performance
        self.Quality = self.Robot.Quality
        self.OEE = self.Robot.OEE

    def sendData2Tangle(self, dt):
        if self.OEE != self.lastOEE:
            self.lastOEE = self.OEE
            msg = 'OEE: {:.3f}, Availabity: {:.3f}, Performance: {:.3f}, Quality: {:.3f} '.\
                format(self.Robot.OEE, self.Robot.Availability, self.Robot.Performance, self.Robot.Quality)
            self.TangleConn.PublishMessage('Machine OEE', msg)
            self.Robot.cursor.execute("""
                    SELECT * FROM today_registers ORDER BY ID DESC;
                    """)
            LastData = self.Robot.cursor.fetchmany(2)
            msg2 = 'ProductionNo: {}, Time to Produce: {}, Status: {}, Quality: {}'.\
                format(LastData[1][1], LastData[1][3], LastData[1][4], LastData[1][5])
            #EDITED TO IOTA STREAMS MQTT GATEWAY FORMAT
            self.TangleConn.PublishMessage('Machine Data', msg2)
            msg3 = {"iot2tangle":[
                        {"sensor":"OEE", "data":[{"Indicator":"{:.3f}".format(self.Robot.OEE)}]},
                        {"sensor":"Availability", "data":[{"Indicator":"{:.3f}".format(self.Robot.Availability)}]},
                        {"sensor":"Performance", "data":[{"Indicator":"{:.3f}".format(self.Robot.Performance)}]},
                        {"sensor":"Quality", "data":[{"Indicator":"{:.3f}".format(self.Robot.Quality)}]},
                        {"sensor":"ProductionNo", "data":[{"Total":"{}".format(LastData[1][1])}]},
                        {"sensor":"TimetoProduce", "data":[{"seconds":"{}".format(LastData[1][3])}]},
                        {"sensor":"Status", "data":[{"Ended?":"{}".format(LastData[1][4])}]},
                        {"sensor":"Quality", "data":[{"Good?":"{}".format(LastData[1][5])}]}],
                        "device":"MACHINE_OEE","timestamp":"{}".format(time.time())}
            self.TangleConn.PublishMessage('iot2tangle', json.dumps(msg3))


    def getDataStoped(self, dt):
        pass

    def set_time(self, dt):
        self.your_time = time.strftime('%H:%M')
        self.your_date = time.strftime('%d/%m/%y')

    def atualiza(self, dt):
        #OEE
        if self.OEE >= .70:
            self.OEE_Color = get_color_from_hex('#8CF153')
        elif self.OEE >= .50:
            self.OEE_Color =  get_color_from_hex('#F5EE0E')
        elif self.OEE < .50:
            self.OEE_Color =  get_color_from_hex('#CD0505')
        # Availability
        if self.Availability >= .70:
            self.Availability_Color = get_color_from_hex('#8CF153')
        elif self.Availability >= .50:
            self.Availability_Color = get_color_from_hex('#F5EE0E')
        elif self.Availability < .50:
            self.Availability_Color = get_color_from_hex('#CD0505')
        # Performance
        if self.Performance >= .70:
            self.Performance_Color = get_color_from_hex('#8CF153')
        elif self.Performance >= .50:
            self.Performance_Color = get_color_from_hex('#F5EE0E')
        elif self.Performance < .50:
            self.Performance_Color = get_color_from_hex('#CD0505')
        # Quality
        if self.Quality >= .70:
            self.Quality_Color = get_color_from_hex('#8CF153')
        elif self.Quality >= .50:
            self.Quality_Color = get_color_from_hex('#F5EE0E')
        elif self.Quality < .50:
            self.Quality_Color = get_color_from_hex('#CD0505')

#Inicialização da Aplicação
if __name__=='__main__':
    s4boee().run()
