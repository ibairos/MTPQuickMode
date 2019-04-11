#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Sender part for the Quick Mode competition of Team B
# This version uses STOP&WAIT with timeout if the ACK is not received
# It also uses CRC to ensure packet integrity
# Date: 10/04/2019
# Version: 1.0

import RPi.GPIO as GPIO
from lib_nrf24 import NRF24
import time
import spidev
import sys
import os
import crc16

# Initialize GPIOs
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define the pipes that will be used to send the data from one transceiver to the other
pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]


def initialize_radios(csn, ce, channel):
    """ This function initializes the radios, each
    radio being the NRF24 transceivers.
    
    It gets 3 arguments, csn = Chip Select, ce = Chip Enable
    and the channel that will be used to transmit or receive the data."""

    radio = NRF24(GPIO, spidev.SpiDev())
    radio.begin(csn, ce)
    time.sleep(2)
    radio.setRetries(15, 15)
    radio.setPayloadSize(32)
    radio.setChannel(channel)

    radio.setDataRate(NRF24.BR_250KBPS)
    radio.setPALevel(NRF24.PA_MIN)
    radio.setAutoAck(False)
    radio.enableDynamicPayloads()
    radio.enableAckPayload()

    return radio


def num_generator(num):
    """ We must ensure that we always send 2 bytes 
    to control the frames."""

    num = str(num)
    if len(num) == 1:
        return '0'+num
    elif len(num) == 2:
        return num
    else:
        print('There was a problem with the number generator')


def ensure_crc(crc):
    """ In final designs it was found that some text inputs
    would generate crc lengths smaller than 5 (which is the usual one),
    so this function ensures we always send 5 bytes through the antenna."""

    crc = str(crc)
    if len(crc) == 1:
        return '0000'+crc
    elif len(crc) == 2:
        return '000'+crc
    elif len(crc) == 3:
        return '00'+crc
    elif len(crc) == 4:
        return '0'+crc
    elif len(crc) == 5:
        return crc
    else:
        print('There was a problem with the number ensure_crc')


def calculate_crc(chunk):
    """ This function calculates the CRC for the given data. """

    return ensure_crc(crc16.crc16xmodem(chunk))


def send_packet(sender, payload):
    """ Send the packet thorugh the sender radio. """
    sender.write(payload)


def ack_or_timeout(receiver):
    """ This is a blocking function that waits until
    data has been received or until the defined timeout has passed. """

    timeout_starts = time.time() 
    while not receiver.available(pipes[0]) and (time.time() - timeout_starts) < 0.01:
        time.sleep(0.01)


def read_file(file_path):
    """ Gets the provided file and reads its content as bytes,
    after that, it stores everything in the variable payload_list,
    which it returns. """

    payload_list = list()

    if os.path.isfile(file_path):
        print("Loading File in: " + file_path)

        with open(file_path, 'rb') as f:
            count = 0
            while True:
                chunk = f.read(25) 
                if chunk:
                    if count == 100:
                        count = 0
                    num = num_generator(count)
                    crc = calculate_crc(chunk+bytes(num.encode('utf-8')))
                    count = count + 1
                    payload_list.append(chunk+bytes(num.encode('utf-8'))+bytes(crc.encode('utf-8')))
                else:
                    break
    else:
        print("ERROR: file does not exist in PATH: " + file_path)
    
    return payload_list


def main():
    """ This main function initializes the radios and sends
    all the data gathered from the file. """

    radio = initialize_radios(0, 25, 0x60)

    radio.openWritingPipe(pipes[1])
    radio.openReadingPipe(0, pipes[0])

    print("Sender Information")
    radio.printDetails()

    payload_list = read_file(sys.argv[1])

    count = 0
    while count < len(payload_list):
        # send a packet to receiver
        acknowledged = False
        while not acknowledged:
            send_packet(radio, payload_list[count])
            print("Sent payload number: " + str(count))

            # Did we get an ACK back?
            radio.startListening()
            ack_or_timeout(radio)
            
            if radio.available(pipes[0]):
                recv_buffer = []
                radio.read(recv_buffer, radio.getDynamicPayloadSize())
                ack_received = bytes(recv_buffer)
                if ack_received == b'1GUTACK':
                    acknowledged = True
                    count = count + 1
            radio.stopListening()

    while True:
        print("Sending the FinalACK")
        time.sleep(1)
        send_packet(radio, b'TH1SPR0GRAMSHOULDBEOVER9999999')

        # Did we get an ACK back?
        radio.startListening()
        ack_or_timeout(radio)

        if radio.available(pipes[0]):
            recv_buffer = []
            radio.read(recv_buffer, radio.getDynamicPayloadSize())
            received = bytes(recv_buffer)
            if received == b'TH1SISTH3FINALACK':
                break
        radio.stopListening()

    print("File sent successfully")
        

if __name__ == '__main__':
    main()
