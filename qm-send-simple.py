#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Receiver part for the Quick Mode competition of Team B
# This version uses STOP&WAIT with timeout if the ACK is not received
# It also uses CRC to ensure packet integrity
# Date: 10/04/2019
# Version: 1.0

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
from lib_nrf24 import NRF24
import spidev
import sys
import os
import time

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


def send_packet(sender, payload):
    """ Send the packet through the sender radio. """
    sender.write(payload)


def read_file(file_path):
    """ Gets the provided file and reads its content as bytes,
    after that, it stores everything in the variable payload_list,
    which it returns. """

    payload_list = list()

    if os.path.isfile(file_path):
        print("Loading File in: " + file_path)
        with open(file_path, 'rb') as f:
                chunk = f.read(25)
                payload_list.append(chunk)
    else:
        print("ERROR: file does not exist in PATH: " + file_path)

    return payload_list


def main():
    """ This main function initializes the radios and sends
    all the data gathered from the file. """

    sender = initialize_radios(0, 25, 0x60)

    sender.openWritingPipe(pipes[1])

    print("Sender Information")
    sender.printDetails()

    payload_list = read_file(sys.argv[1])
    send_packet(sender, payload_list[0])
    print("Packet Sent ")


if __name__ == '__main__':
    main()
