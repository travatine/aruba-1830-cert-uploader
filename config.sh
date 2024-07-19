# point at your existing private key file OR if this does not exist a certificate is generated.
PRIVATE_RSA_KEY_FILE="./certs/private.key.pem";

# The following file will be created based on private key
PUBLIC_RSA_KEY_FILE="./certs/public.key.pem";

CERTDIR="./certs"

# The certificate file ( if it does not already exist, a self signed certificate is generated)
CERT_FILE="./certs/cert.pem";

# Certificate details (if using self signed)
COUNTRY="AU";
STATE="WA";
LOCALITY="PERTH";
ORGNAME="OZZIELAN";
COMMONNAME="SELFSIGNEDCERT";
