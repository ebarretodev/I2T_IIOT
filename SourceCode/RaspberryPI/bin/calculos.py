from bin.mitubishifx5 import PLC
from kivy.properties import NumericProperty, ListProperty, DictProperty
import time
import sqlite3

class Machine():
    def __init__(self, limitTime, standardTime):
        self.conn = sqlite3.connect('database/Producao.db')
        self.cursor = self.conn.cursor()
        self.limitTime = limitTime
        self.standardTime = standardTime
        # self.clp = PLC('FX5CPU', '192.168.3.250', 3000)
        # self.clp.connectPLC()
        self.MachineProduce = 0
        self.lastMachineProduce = 0
        self.TimesRegisters = []
        self.TimesProductionRegisters = []
        self.TimesStoppedRegisters = []
        self.StopDetected = 0
        self.StopRegistered = 0
        self.StopRegisteredReason = {}
        self.NotRegisterStopped = 0
        self.GoodParts = 0
        self.lastGoodParts = 0
        self.GoodPartsElements = []
        self.Availability = 0
        self.Performance = 0
        self.Quality = 0
        self.OEE = 0


    def checkProducing(self, dt):
        try:

            self.cursor.execute("""CREATE TABLE today_registers (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            last_produced INT,
            time_ocurred REAL NOT NULL,
            time_elapsed REAL,
            status TEXT,
            quality INT
            );
            """)
            self.conn.commit()
        except:
            pass
        # self.MachineProduce = self.clp.read_D(0)
        self.cursor.execute("""
        SELECT * FROM today_registers ORDER BY ID DESC;
        """)
        self.lastMachineProduce = self.cursor.fetchmany(2)

        if self.lastMachineProduce == []:
            now = time.time()
            self.cursor.execute("""
                                    INSERT INTO today_registers VALUES (Null, :value, :time, Null, Null, Null);
                                    """, {'time': now, 'value': self.MachineProduce})
            self.conn.commit()
        elif self.lastMachineProduce != None:
            if self.MachineProduce == self.lastMachineProduce[0][1]:
                try:
                    time_elapsed = self.lastMachineProduce[0][2] - self.lastMachineProduce[1][2]
                    self.cursor.execute("""
                        UPDATE today_registers
                        SET time_elapsed = :time_elapsed, status = 'done'
                        WHERE id = :id ;
                    """, {'id': self.lastMachineProduce[1][0], 'time_elapsed': time_elapsed})
                    self.conn.commit()
                except:
                    pass
            elif self.MachineProduce != self.lastMachineProduce[0][1]:

                now = time.time()
                self.cursor.execute("""
                        INSERT INTO today_registers VALUES (Null, :value, :time, Null, 'producing', Null);
                        """, {'time':now, 'value': self.MachineProduce})
                self.conn.commit()


    def checkGoodParts(self, dt):
        # self.GoodParts = self.clp.read_D(1)
        self.cursor.execute("""
                SELECT * FROM today_registers ORDER BY ID DESC;
                """)
        list = self.cursor.fetchmany(2)
        try:
            if self.GoodParts != self.lastGoodParts:
                self.lastGoodParts = self.GoodParts
                self.cursor.execute("""
                    UPDATE today_registers
                    SET quality = 'good'
                    WHERE id = :id;
                """, {'id': list[1][0]})
                self.conn.commit()
        except:
            pass


    def CalcIndicators(self, dt):
        self.cursor.execute("SELECT * FROM today_registers")
        list = self.cursor.fetchall()
        total_good_parts = 0
        total_done_parts = 0
        total_done_elapsedtime = 0
        total_error = 0
        total_error_elapsedtime = 0

        for row in list:
            if row[5] == 'good':
                total_good_parts += 1
            if row[4] == 'done':
                total_done_parts +=1
                total_done_elapsedtime += row[3]
            if row[4] == 'error':
                total_error += 1
                total_error_elapsedtime += row[3]
        try:
            self.Availability = total_done_elapsedtime / (total_done_elapsedtime + total_error_elapsedtime)
            self.Performance = self.standardTime / (total_done_elapsedtime/total_done_parts)
            self.Quality = total_good_parts / total_done_parts
            self.OEE = self.Availability * self.Performance * self.Quality
        except:
            pass

