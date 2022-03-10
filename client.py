import socket
import threading
import pickle
import sys
import datetime

state = {}


def serverListen(server):
    while True:
        msg = server.recv(1024).decode('ascii')
        if msg == "/messageSend":
            server.send(bytes(state['receivers'], "utf-8"))
            server.recv(1024)
            server.send(bytes(state["userInput"], "utf-8"))
            server.recv(1024)
            server.send(bytes(state["groupName"], "utf-8"))
            if state["groupName"] == "None":
                print("[" + datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S.%f") + "] Sent to " + state[
                    'receivers'] + ": " + state["userInput"])
        elif msg == "/groupName":
            server.send(bytes(state['groupName'], "utf-8"))
        elif msg == "/joinGroup":
            server.send(bytes(state['groupName'], "utf-8"))
        elif msg == "/createGroup":
            server.send(bytes(state['groupName'], "utf-8"))
        elif msg == "/kickMember":
            server.send(bytes(state['groupName'], "utf-8"))
            server.recv(1024)
            server.send(bytes(state['groupMember'], "utf-8"))
        elif msg == "/disconnect":
            server.send(bytes(datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S.%f"), "utf-8"))
            break
        else:
            print(msg)


def userInput(server):
    while True:
        message = input("")
        state['userInput'] = message
        if message == "Kick member":
            state['groupName'] = input("Enter the name of the group: ")
            state['groupMember'] = input("Enter the name of the member: ")
            server.send(b"/kickMember")
        elif message == "Change group name":
            state['groupName'] = input("Enter the old and new name of the group: ")
            server.send(b"/groupName")
        elif message == "Join group":
            state['groupName'] = input("Enter the name of the group to join: ")
            server.send(b"/joinGroup")
        elif message == "Create group":
            state['groupName'] = input("Enter the name of the group to create: ")
            server.send(b"/createGroup")
        elif message == "Disconnect":
            server.send(b"/disconnect")
            break
        else:
            state['receivers'] = input("Enter the names of receivers or All to broadcast within a group: ")
            state['groupName'] = input("Enter the name of the group where to send or None if its a personal message: ")
            server.send(b"/messageSend")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect(('127.0.0.1', 55567))

    name = input("Your name: ")
    server.send(name.encode('ascii'))

    serverListenThread = threading.Thread(target=serverListen, args=(server,))
    serverListenThread.start()

    userInputThread = threading.Thread(target=userInput, args=(server,))
    userInputThread.start()


if __name__ == "__main__":
    main()
