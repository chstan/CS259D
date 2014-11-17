import sys
import socket
import string
import time
import select
import math

irc_host = "chat.freenode.net"
irc_port = 6667
max_channel_age = 100000
irc_nick = "candc"
channel = "#holpgknlxo"



def get_channel_number():
    return int(math.floor(time.time())) / max_channel_age

def simple_hash(a):
    prime = 32416189063
    mult = 569059615
    return (a * mult) % prime


def generate_channel_name():
    num = get_channel_number()
    bit_a = simple_hash(num)
    bit_b = simple_hash(bit_a)
    bit_c = simple_hash(bit_b)
    bit_d = simple_hash(bit_c)
    bit_e = simple_hash(bit_d)
    char_1 = bit_b & ((2**32) - 1)
    char_2 = bit_c & ((2**32) - 1)
    char_3 = bit_d & ((2**32) - 1)
    char_4 = bit_e & ((2**32) - 1)
    return ("#%08x%08x%08x%08x" % (char_1, char_2, char_3, char_4))

def irc_receive(irc_socket):
    if (irc_socket == None):
        setup_irc()
    is_ready = select.select([irc_socket], [], [], 1)
    if not is_ready[0]:
        return []
    buffered_lines = irc_socket.recv(8192)
    lines = buffered_lines.split("\n")
    lines = [str(l).strip() for l in lines if str(l).strip() != '']
    return lines

def irc_parse_line(line):
    # ALSO RESPOND TO PINGS
    msg_sep = "PRIVMSG " + channel + " :"
    splits = line.split(msg_sep, 1)
    if len(splits) == 1:
        print("Rejecting %s" % line)
        return None
    return splits[1]

def irc_parse_all_lines(lines):
    return filter(None, [irc_parse_line(line) for line in lines])

def irc_send(irc_socket, msg):
    if (irc_socket == None):
        setup_irc()
    print("> " + msg) # maybe not desirable behavior
    irc_socket.send(msg + "\r\n")

def irc_channel_send(irc_socket, msg):
    irc_send(irc_socket, "PRIVMSG %s :%s" % (channel, msg))

def setup_irc():
    irc_socket = socket.socket()
    irc_socket.connect((irc_host, irc_port))
    irc_socket.setblocking(0)
    irc_send(irc_socket, "NICK %s" % irc_nick)
    irc_send(irc_socket, "USER %s %s %s :%s" % (irc_nick, irc_nick, irc_nick, irc_nick))
    irc_send(irc_socket, "PRIVMSG R : Login <>")
    irc_send(irc_socket, "MODE %s + x" % irc_nick)
    irc_send(irc_socket, "JOIN %s" % channel)
    return irc_socket

if __name__ == "__main__":
    channel = generate_channel_name()
    irc_socket = setup_irc()
    irc_channel_send(irc_socket, "Hello.")
    while True:
        received = irc_receive(irc_socket)
        received = irc_parse_all_lines(received)
        out = "\n".join(received)
        if out:
             print out
