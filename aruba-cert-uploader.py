import json
import os
import requests
import ssl

import requests
import xml.etree.ElementTree as ET

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_PKCS1_v1_5
import binascii

from xml.etree.ElementTree import Element, SubElement, tostring
from urllib.parse import urlparse

import datetime

class ArubaSwitch:

    def __init__(self,hostName: str, port:int, user: str, password: str) -> None:
        self.hostName = hostName
        self.port = port
        self.user = user
        self.password = password
        self.session =  requests.Session()
        self.magic=None

    def __debug(self,message:str):
        print(f'DEBUG { datetime.datetime.now()} {message}')

    def _getURL(self, url:str):
        self.__debug(f'GET {url}')
        result = self.session.get(url)
        self.__debug(f'GET Done.')
        return result

    def _getMagic(self):
        if self.magic is None:
            result = self._getURL(f'http://{self.hostName}/')
            if result:
                a = urlparse(result.url)
                self.magic = a.path.split('hpe/')[0]
        return self.magic

    def encrypt_data(self,publicKey,data:str):
        key = RSA.importKey(publicKey)
        cipher = Cipher_PKCS1_v1_5.new(key)
        return cipher.encrypt(data.encode())

    def bin2hex(self,binStr):
        return binascii.hexlify(binStr)

    def _encryptionSettingsGetPasswordEncryptEnable(self,root: Element):
        passwEncryptEnable = root.find('.//passwEncryptEnable')
        if passwEncryptEnable is None:
            return False
        else:
            passwEncryptEnable=passwEncryptEnable.text
            return passwEncryptEnable == '1'

    def _encryptionSettingsGetPublicKey(self,root:Element):
        publicKey = root.find('.//rsaPublicKey')
        if publicKey is None:
            raise RuntimeError('Error publicKey missing from encyption settings')
        return publicKey.text

    def _encryptionSettingsGetLoginToken(self, root:Element):
        loginToken = root.find('.//loginToken')
        if loginToken is None:
            raise RuntimeError('Could not get Login token!')
        return loginToken.text

    def _resultExtractStatus(self,resultStr):
        root = ET.fromstring(resultStr)
        statusCode = root.find('.//statusCode')
        statusString = root.find('.//statusString')

        if statusCode is not None:
            statusCode = statusCode.text
        else:
            statusCode = 500

        if statusString is not None:
            statusString = statusString.text
        else:
            statusString = 'ERRORS'
        return int(statusCode), statusString

    def parseEncryptionSettings(self,hostname,xml,username,password):
        root = ET.fromstring(xml)

        if not self._encryptionSettingsGetPasswordEncryptEnable(root):
             newPath = './system.xml?action=login&user=' + username + '&password=' + password + "&ssd=true&"
        else:
            publicKey = self._encryptionSettingsGetPublicKey(root)
            loginToken = self._encryptionSettingsGetLoginToken(root)
            res = self.encrypt_data(publicKey,f'user={username}&password={password}&ssd=true&token={ loginToken }&')
            res = self.bin2hex(res)
            res= res.decode()
            newPath = './system.xml?action=login&cred=' + res

        result = self._getURL(f'http://{hostname}/{newPath}')
        if result.ok:
            code, errorMessage = self._resultExtractStatus(result.text)
            if code > 0:
                raise RuntimeError(f'ERROR statusCode={code} {errorMessage} ')
            return True
        raise RuntimeError(f'ERROR failed to log on {result.text}')

    def authenticate(self):
        self.__debug('>> authenticate')
        r = self._getURL(f'http://{self.hostName}/device/wcd?{{EncryptionSetting}}'   )
        if not r:
            raise RuntimeError('ERROR authenticate - Could not load encryption settings from switch')
        xml = r.text
        return self. parseEncryptionSettings(self.hostName,xml,self.user,self.password)

    def loadPrivateKey(self,privateKeyFile):
        privateKey = []
        with open(privateKeyFile,'r') as f:
            privateKey = f.readlines()
        privKey =''
        for line in privateKey:
            privKey=privKey+(line) 
        return privKey.strip()

    def loadPublicKey(self,publicKeyFile):
        publicKey = []
        with open(publicKeyFile,'r') as f:
            publicKey = f.readlines()
        pubKey =''
        for line in publicKey:
            pubKey=pubKey+(line) 
        return pubKey.strip()

    def loadCertificate(self,certificateFile):
        certificate = []
        with open(certificateFile,'r') as f:
            certificate = f.readlines()
        cert =''
        for line in certificate:
            cert=cert+(line ) 
        return cert.strip()

    def generateCertificateXML(self, privateKeyText, publicKeyText, certificateText):
        deviceConfiguration = Element('DeviceConfiguration')
        SSLCryptoCertificateImportList = SubElement(deviceConfiguration, "SSLCryptoCertificateImportList")
        SSLCryptoCertificateImportList.set('action','set')
        Entry = SubElement(SSLCryptoCertificateImportList,'Entry')
        instance = SubElement(Entry,'instance')
        instance.text='1'
        certificate = SubElement(Entry,'certificate')
        certificate.text = certificateText
        publicKey = SubElement(Entry,'publicKey')
        publicKey.text = publicKeyText
        privateKeySSDType = SubElement(Entry,'privateKeySSDType')
        privateKeySSDType.text='3'
        privateKey = SubElement(Entry,'privateKey')
        privateKey.text = privateKeyText
        return tostring(deviceConfiguration).decode()

    def uploadSSLCertificate(self, privateKeyFile, publicKeyFile, certificateFile):
        privKey = self.loadPrivateKey(privateKeyFile)
        pubKey = self.loadPublicKey(publicKeyFile)
        cert = self.loadCertificate(certificateFile)

        xml = self.generateCertificateXML(privKey,pubKey,cert)
        xmlHeader="<?xml version=\'1.0\' encoding=\'utf-8\'?>"
        data= (xmlHeader+xml)
        url = f'http://{self.hostName}/{self._getMagic()}/hpe/wcd?{{EWSGlobalSetting}}{{SSLCryptoCertificateList}}{{SSLCryptoCertificateImportList}}'
        result = self.session.post(url, data)
        print(result.text)

# code starts here
print('loading certificate config...')

with open('config.json') as f:
  config = json.load(f)
  privateKeyFile = config['certificates']['privateKeyFile']
  publicKeyFile = config['certificates']['publicKeyFile']
  certificateFile = config['certificates']['certificateFile']
  switches = config['switches']
  for switch in switches:
    hostname=switch['hostname']
    user=switch['user']
    password=switch['password']

    try:
      aSwitch = ArubaSwitch(hostname,443,user,password)
      if aSwitch.authenticate():
        aSwitch.uploadSSLCertificate(privateKeyFile,publicKeyFile,certificateFile)
        print(f'Uploaded Certificate to https://{hostname}/')
    except RuntimeError as e:
      print(e)
