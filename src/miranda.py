#!/usr/bin/env python
################################
# Interactive UPNP application #
# Craig Heffner                #
# 07/16/2008                   #
################################

import sys
import os
import re
import platform
import xml.dom.minidom as minidom
import IN
import urllib.request, urllib.parse, urllib.error
#import urllib3
import readline
import time
import pickle
import struct
import base64
import getopt
import select
from socket import *



#UPNP class for getting, sending and parsing SSDP/SOAP XML data (among other things...)
class upnp:
	ip = False
	port = False
	completer = False
	msearchHeaders = {
		'MAN' : '"ssdp:discover"',
		'MX'  : '2'
	}
	DEFAULT_IP = "239.255.255.250"
	DEFAULT_PORT = 1900
	UPNP_VERSION = '1.0'
	MAX_RECV = 8192
	MAX_HOSTS = 0
	TIMEOUT = 0
	HTTP_HEADERS = []
	ENUM_HOSTS = {}
	VERBOSE = False
	UNIQ = False
	DEBUG = False
	LOG_FILE = False
	BATCH_FILE = None
	IFACE = None
	STARS = '****************************************************************'
	csock = False
	ssock = False

	def __init__(self, ip=False, port=False, iface=None, appCommands=[]):
		if appCommands:
			self.completer = CmdCompleter(appCommands)
		if self.initSockets(ip,port,iface) == False:
			print ('UPNP class initialization failed!')
			print ('Bye!')
			sys.exit(1)
		else:
			self.soapEnd = re.compile('<\/.*:envelope>')

	#Initialize default sockets
	def initSockets(self,ip,port,iface):
		if self.csock:
			self.csock.close()
		if self.ssock:
			self.ssock.close()

		if iface != None:
			self.IFACE = iface
		if not ip:
			ip = self.DEFAULT_IP
		if not port:
			port = self.DEFAULT_PORT
		self.port = port
		self.ip = ip
		
		try:
			#This is needed to join a multicast group
			self.mreq = struct.pack("4sl",inet_aton(ip),INADDR_ANY)

			#Set up client socket
			self.csock = socket(AF_INET,SOCK_DGRAM)
			self.csock.setsockopt(IPPROTO_IP,IP_MULTICAST_TTL,2)
			
			#Set up server socket
			self.ssock = socket(AF_INET,SOCK_DGRAM,IPPROTO_UDP)
			self.ssock.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)

			# BSD systems also need to set SO_REUSEPORT		
			try:
				self.ssock.setsockopt(SOL_SOCKET,SO_REUSEPORT,1)
			except:
				pass

			#Only bind to this interface
			if self.IFACE != None:
				print ('\nBinding to interface',self.IFACE,'...\n')
				self.ssock.setsockopt(SOL_SOCKET,IN.SO_BINDTODEVICE,struct.pack("%ds" % (len(self.IFACE)+1,), self.IFACE))
				self.csock.setsockopt(SOL_SOCKET,IN.SO_BINDTODEVICE,struct.pack("%ds" % (len(self.IFACE)+1,), self.IFACE))

			try:
				self.ssock.bind(('',self.port))
			except Exception (e):
				print ("WARNING: Failed to bind %s:%d: %s" , (self.ip,self.port,e))
			try:
				self.ssock.setsockopt(IPPROTO_IP,IP_ADD_MEMBERSHIP,self.mreq)
			except Exception (e):
				print ('WARNING: Failed to join multicast group:',e)
		except Exception (e):
			print ("Failed to initialize UPNP sockets:",e)
			return False
		return True

	#Clean up file/socket descriptors
	def cleanup(self):
		if self.LOG_FILE != False:
			self.LOG_FILE.close()
		self.csock.close()
		self.ssock.close()

	#Send network data
	def send(self,data,socket):
		#By default, use the client socket that's part of this class
		if socket == False:
			socket = self.csock
		try:
			socket.sendto(data,(self.ip,self.port))
			return True
		except Exception (e):
			print ("SendTo method failed for %s:%d : %s" % (self.ip,self.port,e))
			return False

	#Receive network data
	def recv(self,size,socket):
		if socket == False:
			socket = self.ssock

		if self.TIMEOUT:
			socket.setblocking(0)
			ready = select.select([socket], [], [], self.TIMEOUT)[0]
		else:
			socket.setblocking(1)
			ready = True
	
		try:	
			if ready:
				return socket.recv(size)
			else:
				return False
		except:
			return False

	#Send SOAP request
	def sendSOAP(self,hostName,serviceType,controlURL,actionName,actionArguments):
		argList = ''
		soapResponse = ''

		if '://' in controlURL:
			urlArray = controlURL.split('/',3)
			if len(urlArray) < 4:
				controlURL = '/'
			else:
				controlURL = '/' + urlArray[3]


		soapRequest = 'POST %s HTTP/1.1\r\n' % controlURL

		#Check if a port number was specified in the host name; default is port 80
		if ':' in hostName:
			hostNameArray = hostName.split(':')
			host = hostNameArray[0]
			try:
				port = int(hostNameArray[1])
			except:
				print ('Invalid port specified for host connection:',hostName[1])
				return False
		else:
			host = hostName
			port = 80

		#Create a string containing all of the SOAP action's arguments and values
		for arg,(val,dt) in actionArguments.items():
			argList += '<%s>%s</%s>' % (arg,val,arg)

		#Create the SOAP request
		soapBody = 	'<?xml version="1.0"?>\n'\
				'<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n'\
				'<SOAP-ENV:Body>\n'\
				'\t<m:%s xmlns:m="%s">\n'\
				'%s\n'\
				'\t</m:%s>\n'\
				'</SOAP-ENV:Body>\n'\
				'</SOAP-ENV:Envelope>' % (actionName,serviceType,argList,actionName)

		#Specify the headers to send with the request
		headers = 	{
			'Content-Type':'text/xml; charset="utf-8"',
			'SOAPACTION':'"%s#%s"' % (serviceType,actionName),
			'Content-Length': len(soapBody),
			'HOST':hostName,
			'User-Agent': 'CyberGarage-HTTP/1.0',
				}

		#Generate the final payload
		for head,value in headers.items():
			soapRequest += '%s: %s\r\n' % (head,value)
		soapRequest += '\r\n%s' % soapBody

		#Send data and go into recieve loop
		try:
			sock = socket()
			sock.connect((host,port))
			sock.send(soapRequest.encode())
			while True:
				data = sock.recv(self.MAX_RECV).decode()
				if not data:
					break
				else:
					soapResponse += data
					if self.soapEnd.search(soapResponse.lower()) != None:
						break
			sock.close()

			(header,body) = soapResponse.split('\r\n\r\n',1)
			if not header.upper().startswith('HTTP/1.') and ' 200 ' in header.split('\r\n')[0]:
				print ('SOAP request failed with error code:',header.split('\r\n')[0].split(' ',1)[1])
				errorMsg = self.extractSingleTag(body,'errorDescription')
				if errorMsg:
					print ('SOAP error message:',errorMsg)
				return False
			else:
				return body
		except Exception (e):
			print ('Caught socket exception:', e)
			sock.close()
			return False
		except KeyboardInterrupt:
			sock.close()
			return False
