import socket
import threading
import pickle
import os
import sys
import datetime

groups = {}
clientsWithNames = {}
onlineMembers = {}
disconnectTime = {}
bufferedMessages = {}
fileTransferCondition = threading.Condition()


class Group:
    def __init__(self, name, admin, client):
        self.admin = admin
        self.clients = []
        self.allMembers = []
        self.name = name

        self.clients.append(client)
        self.allMembers.append(admin)

    def connect(self, username, client):
        self.allMembers.append(username)
        self.clients.append(client)

    def sendMessage(self, message, username, receivers):
        if receivers == "All":
            for member in self.allMembers:
                if member != username:
                    if member not in onlineMembers.keys():
                        index = self.allMembers.index(username)
                        self.clients[index].send(
                            bytes("The client " + member + " is offline. Last time was seen "
                                  + disconnectTime[member], "utf-8"))
                        if member in bufferedMessages.keys():
                            msgs = bufferedMessages[member].append(
                                bytes("[" + self.name + "] " + username + ": " + message, "utf-8"))
                            bufferedMessages[member] = msgs
                        else:
                            msgs = [bytes("[" + self.name + "] " + username + ": " + message, "utf-8")]
                            bufferedMessages[username] = msgs

                    else:
                        index = self.allMembers.index(member)
                        self.clients[index].send(bytes("[" + self.name + "] " + username + ": " + message, "utf-8"))
        else:
            listRec = list(receivers.split(" "))
            for member in listRec:
                if member not in onlineMembers.keys():
                    index = self.allMembers.index(username)
                    self.clients[index].send(
                        bytes("The client " + member + " is offline. Last time was seen "
                              + disconnectTime[member], "utf-8"))
                    if member in bufferedMessages.keys():
                        msgs = bufferedMessages[member].append(
                            bytes("[" + self.name + "] " + username + ": " + message, "utf-8"))
                        bufferedMessages[member] = msgs
                    else:
                        msgs = [bytes("[" + self.name + "] " + username + ": " + message, "utf-8")]
                        bufferedMessages[username] = msgs
                else:
                    index = self.allMembers.index(member)
                    self.clients[index].send(bytes("[" + self.name + "] " + username + ": " + message, "utf-8"))

    def changeGroupName(self, username, newname):
        if self.admin == username:
            group = groups[self.name]
            del groups[self.name]
            groups[newname] = group
            self.name = newname
            for member in self.allMembers:
                index = self.allMembers.index(member)
                self.clients[index].send(bytes("The new name of group is " + newname, "utf-8"))
        else:
            index = self.allMembers.index(username)
            self.clients[index].send(bytes("You are not an admin and not allowed to change the group name", "utf-8"))

    def kickGroupMember(self, username, groupMember):
        if self.admin == username:
            index = self.allMembers.index(groupMember)
            self.allMembers.pop(index)
            self.clients.pop(index)
            for member in self.allMembers:
                if member != groupMember:
                    index = self.allMembers.index(member)
                    self.clients[index].send(
                        bytes("The group member " + groupMember + " have been kicked out of the group "
                              + self.name, "utf-8"))
                else:
                    index = self.allMembers.index(member)
                    self.clients[index].send(
                        bytes("You have been kicked out of the group " + self.name, "utf-8"))
        else:
            index = self.allMembers.index(username)
            self.clients[index].send(
                bytes("You are not an admin and not allowed to kick members of the group", "utf-8"))


def receive(client, username):
    while True:
        msg = client.recv(1024).decode("utf-8")

        if msg == "/messageSend":
            client.send(b"/messageSend")
            receivers = client.recv(1024).decode("utf-8")
            client.send(b"/sendReceivers")
            message = client.recv(1024).decode("utf-8")
            client.send(b"/sendgroupName")
            groupName = client.recv(1024).decode("utf-8")
            if groupName != "None":
                groups[groupName].sendMessage(message, username, receivers)
            else:
                if receivers not in onlineMembers.keys():
                    client.send(bytes("The client " + receivers + " is offline. Last time was seen "
                                      + disconnectTime[receivers], "utf-8"))
                    if receivers in bufferedMessages.keys():
                        msgs = bufferedMessages[receivers].append(
                            bytes("[" + datetime.datetime.now().strftime("%d-%b-%Y "
                                                                         "%H:%M"
                                                                         ":%S.%f")
                                  + "] Received from " + username + ": " + message, "utf-8"))
                        bufferedMessages[receivers] = msgs
                    else:
                        msgs = [bytes("[" + datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S.%f") +
                                      "] Received from " + username + ": " + message, "utf-8")]
                        print("[" + datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S.%f") +
                              "] Received from " + username + ": " + message)
                        bufferedMessages[receivers] = msgs
                else:
                    result = clientsWithNames[receivers].send(
                        bytes("[" + datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S.%f") +
                              "] Received from " + username + ": " + message, "utf-8"))
                    if result >= 0:
                        client.send(bytes("The message have been sent Successfully", "utf-8"))
                    else:
                        client.send(bytes("The message have been sent Unsuccessfully", "utf-8"))
        elif msg == "/groupName":
            client.send(b"/groupName")
            received = client.recv(1024).decode("utf-8")
            listRec = list(received.split(" "))
            groups[listRec[0]].changeGroupName(username, listRec[1])
        elif msg == "/joinGroup":
            client.send(b"/joinGroup")
            groupJoin = client.recv(1024).decode("utf-8")
            groups[groupJoin].connect(username, client)
            client.send(bytes("You have joined the group " + groupJoin, "utf-8"))
            print("User joined:", groupJoin, "| Name:", username)
        elif msg == "/createGroup":
            client.send(b"/createGroup")
            groupCreate = client.recv(1024).decode("utf-8")
            new_group = Group(groupCreate, username, client)
            groups[groupCreate] = new_group
            client.send(bytes("You have created the group " + groupCreate + " and are now an admin", "utf-8"))
            print("New Group:", groupCreate, "| Admin:", username)
        elif msg == "/kickMember":
            client.send(b"/kickMember")
            groupNameMember = client.recv(1024).decode("utf-8")
            client.send(b"/sendMember")
            groupMember = client.recv(1024).decode("utf-8")
            groups[groupNameMember].kickGroupMember(username, groupMember)
        elif msg == "/disconnect":
            client.send(b"/disconnect")
            time = client.recv(1024).decode("utf-8")
            disconnectTime[username] = time
            del onlineMembers[username]
            print("User Disconnected:", username)
            break
        else:
            print("UNIDENTIFIED COMMAND:", msg)


def handshake(client):
    username = client.recv(1024).decode("utf-8")
    if username in bufferedMessages.keys():
        print("User Reconnected:", username)
        msgs = bufferedMessages[username]
        if len(msgs) > 0:
            i = 0
            while i < len(msgs):
                client.send(msgs[i])
                i = i + 1
    clientsWithNames[username] = client
    onlineMembers[username] = client
    threading.Thread(target=receive, args=(client, username,)).start()


def main():
    host = '127.0.0.1'
    port = 55567

    listenSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listenSocket.bind((host, port))
    listenSocket.listen(10)
    print('Socket is binded to host port')
    print('Socket is listening..')
    while True:
        client, address = listenSocket.accept()
        print("Connected with {}".format(str(address)))

        threading.Thread(target=handshake, args=(client,)).start()


if __name__ == "__main__":
    main()
