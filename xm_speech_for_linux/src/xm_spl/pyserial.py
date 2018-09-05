#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# python serial code from net https://www.cnblogs.com/attentle/p/7098408.html
# https://answers.ros.org/question/85211/importerror-no-module-named-rospkg-on-hydro-solved/
# http://blog.csdn.net/qingche456/article/details/65465760
import threading
import time
import serial
from struct import pack,unpack
import gzip
import binascii
import ast
# serialport class
class ComThread:
    def __init__(self, Port="/dev/ttyUSB2",Baudrate = 115200):#default param
        self.l_serial = None
        self.alive = False
        self.port = Port
        self.baudrate = Baudrate
        # 最终解析出来的接受数据应该为str格式
        self.send_buffer = ""
        self.receive_buffer = ""
        self.port_lock = threading.Lock()
        self.read_lock = threading.Lock()
        self.max_len = 4096
        self.message_type = None
        self.data_len =0
        self.message_ID = None
        self.checknum = 0
        self.data =list()

    # 启动串口并开启读取线程
    def start(self):
        self.l_serial = serial.Serial()
        self.l_serial.port = self.port #"/dev/ttyUSB0"
        self.l_serial.baudrate = self.baudrate #115200
        self.l_serial.timeout = 2 #outtime is 2s 
        self.l_serial.bytesize=serial.EIGHTBITS #8bit
        self.l_serial.stopbits = serial.STOPBITS_ONE # 1bit stopbit
        self.l_serial.parity = serial.PARITY_NONE # no parity
        # serialport is set without flow control by default  
        self.l_serial.open()
        self.state = 0
        if self.l_serial.isOpen():
            self.alive = True
            self.thread_read = threading.Thread(target=self.Reader,  name="reader")
            self.thread_send = threading.Thread(target=self.Sender,name="sender")
            self.thread_read.setDaemon(True)#设置后台运行
            self.thread_send.setDaemon(True)
            self.thread_read.start()
            self.thread_send.start()
            return True
        else:
            return False

   
    def Reader(self):
        while self.alive:
            time.sleep(0.1)
            self.port_lock.acquire()
            self.read_lock.acquire()
            # n is the number reading from the serialport
            n = self.l_serial.inWaiting()
            if n:
                 a= self.l_serial.read(n).hex()
                #  print ("hehe2")
                #  print (a)
                 self.receive_buffer = self.receive_buffer + a#the self.receive_buffer return from the read method is in str() format
            # print ("hehe3\n")
            print (len(self.receive_buffer))
            # print (self.receive_buffer + '\n')
            # time.sleep(0.5)
            if len(self.receive_buffer) > self.max_len*2:
                print ("too long")
                self.receive_buffer = self.receive_buffer[:-self.max_len*2]
            self.read_lock.release()
            self.port_lock.release()

    def Sender(self):
        while self.alive :
            if len(self.send_buffer)%2 ==1 or len(self.send_buffer) ==0:
                self.send_buffer = ""
                pass
            self.port_lock.acquire()
            # 发送一定要注意将str()型的send_buffer转换成bytes()型！！
            # print("the send len is "+str(len(self.send_buffer)))
            self.l_serial.write(bytes.fromhex(self.send_buffer))
            self.port_lock.release()

    def stop(self):
        self.alive = False
        self.thread_read.join()
        self.thread_send.join()
        if self.l_serial.isOpen():
            self.l_serial.close()

# the code below is used for serialport user(API)
    def asyncSend(self,buffer):
        if isinstance(buffer,str):
            self.send_buffer = buffer

    def analysisByte(self): #state machine for serialport
        # data is unsigned char type
        receive_flag = False
        # the reveive_buffer is not good
        self.read_lock.acquire()
        if len(self.receive_buffer) < 2:
            # print (str(len(self.receive_buffer)) + '\n') 
            print ("read length is not enough ")
            self.read_lock.release()
            return receive_flag
        data  = self.receive_buffer[0:2]
        data = unpack('B',bytes.fromhex(data))[0]
        self.receive_buffer = self.receive_buffer[2:]
        self.read_lock.release()
        print ("self.state is "+str(self.state))
        if self.state ==0:
            if pack('B',data).hex().lower() == 'a5':
                self.state +=1
                self.checknum +=data
            else:
                print ("frame head1 is error")
                print (pack('B',data).hex().lower())
                self.checknum =0
                pass
        elif self.state ==1:
            if pack('B',data).hex().lower() =='01':
                self.state +=1
                self.checknum +=data
            else:
                print ("frame head2 is error")                
                self.state =0
                self.checknum =0
        elif self.state ==2:
            self.message_type = data
            self.state +=1
            self.checknum +=data
            
        elif self.state ==3:
            self.data_len = data
            self.state +=1
            self.checknum +=data

        elif self.state ==4:
            temp_len = data
            self.data_len +=temp_len<<8
            self.state +=1
            self.checknum +=data
        
        elif self.state ==5:
            self.message_ID = data
            self.state+=1
            self.checknum +=data
        
        elif self.state ==6:
            temp_ID = data
            self.message_ID +=temp_ID <<8
            self.state +=1
            self.checknum +=data
        
        elif self.state ==7:
            data_temp = pack("B",data).hex()
            self.data.append(data_temp)
            self.checknum +=data
            self.read_lock.acquire()
            data  = self.receive_buffer[0:2*self.data_len-2]
            self.data += data
            data = unpack(str(self.data_len-1)+'B',bytes.fromhex(data))#tuple
            for value in data:
                self.checknum +=value
            self.receive_buffer = self.receive_buffer[2*self.data_len-2:]
            self.read_lock.release()
            self.state +=1
                # self.data_len -=1
                # data_temp = pack("B",data).hex()
                # self.data.append(data_temp)
                # self.checknum +=data
                # if self.data_len ==0:
                #     self.state +=1


        elif self.state ==8:
            self.checknum &=255
            self.checknum  = ~self.checknum +1
            self.checknum &=255
            print(str(self.checknum)+ " is equal with "+str(data))
            if self.checknum == data:
                print ("receive a frame message")
                receive_flag = True
            else:
                print ("check num is error")
            self.checknum =0
            self.state =0

        return receive_flag

    # 发送反馈消息
    def process_recv(self,ID):
        lower_id = ID&255
        high_id = ID//256
        lower_buf = pack('B',lower_id).hex()
        high_buf = pack('B',high_id).hex()
        ack_buf = ['a5','01','ff','04','00',lower_buf,high_buf,'a5','00','00','00']
        check_code =0
        for value in ack_buf:
            num = unpack('B',bytes.fromhex(value))[0]
            check_code +=num
        check_code &=255
        check_code = ~check_code +1
        check_code &=255
        check_buf = pack('B',check_code).hex()
        ack_buf.append(check_buf)
        ack_str = ''.join(ack_buf)
        print (ack_str)
        self.asyncSend(ack_str)


    # 解析消息，并作出回应,如果遇到唤醒反馈，则返回唤醒信息
    def analysisMessage(self):
        result = None
        if self.analysisByte() is False:
            pass
        else:
            # receive a frame message successfully
            self.process_recv(self.message_ID)
            # analysis I receive what?
            if self.message_type == 1:
                # mean shakehand message
                print ("i receive the shakehands message, and i have reply the AIUI")
                self.receive_buffer = ''
                pass
            elif self.message_type == 4:
                # mean the wakeup message, and i want its data
                print ("i receive the wakeup message")
                self.receive_buffer = ''
                # print (self.data)
                analysis_buf = ''.join(self.data)
                uncompress_data = gzip.decompress(binascii.a2b_hex(analysis_buf))
                wakeup_result = uncompress_data.decode('utf-8')
                if isinstance(wakeup_result,str) :
                    print ("i parse the wakeup data successfully ^_^")
                    result = wakeup_result
                    # string->dict
                    result = ast.literal_eval(result)
                    print (result)
                else:
                    print ("the wakeup data is broken")
            else:
                print ("i donnot want these message @_@")

            # here we should init the member
            self.message_type = None
            self.data_len =0
            self.message_ID = None
            self.checknum = 0
            self.data =list()
        return result


# use for test the pyserial function
if __name__ == "__main__":
    ser = ComThread()#use default paramters
   
    if ser.start() == True:
        print ("open the com, and init successfully")
        # 1 test base read function
        # while len(ser.receive_buffer)<400:
        #     pass
        # print (ser.receive_buffer)
        # 2 test shakehands function
        while True:
            if ser.analysisMessage() is not None:
                break
                pass
            # woc without delay the program may broken !!!
            time.sleep(0.2)





            
