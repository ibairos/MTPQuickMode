#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Receiver part for the Quick Mode competition of Team B
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


def write_file(file_path, payload_list):
    """ This function gets the data from the variable payload_list, 
    iterates through it and saves it to the file you have provided 
    in the arguments. 
    
    Warning: If the size of the payload_list is greater than the size
    of the RAM memory this script will fail."""

    with open(file_path, "wb") as f:
        count = 0
        while count < len(payload_list):
            f.write(payload_list[count])
            count = count + 1


def send_packet(sender, payload):
    """ Send the packet through the sender radio. """

    sender.write(payload)


def wait_for_data(receiver):
    """ This is a blocking function that waits
    until data is available in the receiver pipe. """

    while not receiver.available(pipes[1]):
            time.sleep(0.01)


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


def check_crc(chunk, crc):
    """ This function checks if the received CRC is consistent. """

    crc = bytes(crc)
    crc_this = bytes(ensure_crc(crc16.crc16xmodem(bytes(chunk))).encode('utf-8'))
    if crc_this == crc:
        return True
    else:
        return False


def main():
    """ This main function initializes the radios and receives
    all the data available from the sender. """

    sender = initialize_radios(0, 25, 0x70)
    receiver = initialize_radios(0, 25, 0x60)

    sender.openWritingPipe(pipes[0])
    receiver.openReadingPipe(0, pipes[1])

    print("Sender Information")
    sender.printDetails()

    print("Receiver Information")
    receiver.printDetails()

    payload_list = list()
    
    receiver.startListening()

    out = False
    count = 0
    actual_ack = None
    while not out:
        wait_for_data(receiver)

        # recv_buffer is the array where received data will be placed
        recv_buffer = []
        receiver.read(recv_buffer, receiver.getDynamicPayloadSize())
        chunk_and_ack = recv_buffer[:-5]
        ack_num = recv_buffer[-7:-5]
        crc = recv_buffer[-5:]
        data = recv_buffer[:-7]
        ack_num_str = bytes(ack_num).decode('utf-8'
                                            ''
                                            ''
                                            ''
                                            ''
                                            ''
                                            ''
                                            ''
                                            ''
                                            ''
                                            ''
                                            ''
                                            ''
                                            ''
                                            )
        data_str = bytes(data)

        if (actual_ack != ack_num_str) and (data_str != b'TH1SPR0GRAMSHOULDBEOVER'):
            if check_crc(chunk_and_ack, crc):
                send_packet(sender, b'1GUTACK')
                payload_list.append(bytes(data))
                actual_ack = ack_num_str
                print("Sent ACK number " + str(count))
                count = count + 1
            else: 
                send_packet(sender, b'1BATACK')
        elif (actual_ack == ack_num_str) and (data_str != b'TH1SPR0GRAMSHOULDBEOVER'):
            send_packet(sender, b'1GUTACK')
        elif (actual_ack != ack_num_str) and data_str == b'TH1SPR0GRAMSHOULDBEOVER':
            print("Finishing Script")
            time.sleep(0.5)
            send_packet(sender, b'TH1SISTH3FINALACK')
            out = True

    write_file(sys.argv[1], payload_list)


if __name__ == '__main__':
    main()
