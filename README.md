# aruba-1830-cert-uploader
A tool to upload certificates to my aruba 1830 switches

## Configuring

config.sh - this file is loaded by setup.sh
 - Specify the location of your private key file & certificate
config.json - this file is loaded by aruba-cert-uploader.py
- Specify the hostname & credentials of your switches

## Setting up, Converting keys and Uploading Certificates

  ./setup.sh

  This bash script will: 
  - check openssl is installed
  - Set up a Python venv
  - Create an RSA Public key
  - Upload a certificate to the switch
    - If no certificate exists, a self-signed certificate is generated.
   
## Notes

This process has been tested on Arube 1830 switches running Firmware Version 2.9.1 with both Self Signed Certificates & Certificates from Lets Encrypt.

