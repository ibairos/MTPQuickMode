#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Receiver part for the Quick Mode competition of Team C
# This version uses STOP&WAIT with timeout if the ACK is not received
# It also uses CRC to ensure packet integrity
# Author: Arnau E.
# Date: 23/10/2018
# Version: 1.6

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
from lib_nrf24 import NRF24
import time
import spidev
import sys
import os

# Define the pipes that will be used to send the data from one transceiver to the other
pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]


def initialize_radios(csn, ce, channel):
    ''' This function initializes the radios, each
    radio being the NRF24 transceivers.

    It gets 3 arguments, csn = Chip Select, ce = Chip Enable
    and the channel that will be used to transmit or receive the data.'''

    radio = NRF24(GPIO, spidev.SpiDev())
    radio.begin(csn, ce)
    time.sleep(2)
    radio.setRetries(15, 15)
    radio.setPayloadSize(32)
    radio.setChannel(channel)

    radio.setDataRate(NRF24.BR_2MBPS)
    radio.setPALevel(NRF24.PA_MIN)
    radio.setAutoAck(False)
    radio.enableDynamicPayloads()
    radio.enableAckPayload()

    return radio


def write_file(file_path, payload_list):

    with open(file_path, "wb") as f:
        f.write(payload_list[0])

def wait_for_data(receiver):
    while not receiver.available(pipes[1]):
        time.sleep(0.01)


def main():
    receiver = initialize_radios(0, 25, 0x60)
    receiver.openReadingPipe(0, pipes[1])

    print("Receiver Information")
    receiver.printDetails()

    payload_list = list()

    receiver.startListening()
    wait_for_data(receiver)
    data=[]
    receiver.read(data, receiver.getDynamicPayloadSize())
    payload_list.append(bytes(data))
    write_file(sys.argv[1], payload_list)

if __name__ == '__main__':
    main()

