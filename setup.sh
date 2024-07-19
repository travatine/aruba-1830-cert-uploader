#!/usr/bin/env -S bash -e -u  -o pipefail

#
# Check if OpenSSL installed and exit if not.
#
check_openssl_installed() {
  echo 'Checking if openssl installed...';
  if [ ! -f /usr/bin/openssl ]; then
    echo 'Please install openssl';
    echo 'e.g. sudo apt install -y openssl';
    echo ' or sudo dnf install -y openssl';
    exit 8;
  fi
}

#
# Create a Python Venv with the dependencies to run the certificate uploader
#
create_venv() {
  echo 'Creating venv...';
  python3 -m venv myenv;

  echo 'activating venv...';
  . myenv/bin/activate;

  echo 'installing dependencies'
  pip3 install -q -r requirements.txt;
}

#
# This will convert Lets Encrypt Certificate to Aruba Instant On Compatible Format
#
create_rsa_pubkey_file() {
  local in_private_key_file="$1";
  local out_public_key_file="$2";

  # Check the private key exists
  if [ ! -f $in_private_key_file ]; then
    echo "Private key file $in_private_key_file not found - Generating Self Signed Certificate...";
    openssl genrsa -traditional -out $in_private_key_file 3072;
  fi
  echo 'Extracting RSA Public Key from private key...'
  openssl rsa -in $in_private_key_file -pubout -out temp.out.pubkey.pem -traditional;

  # Convert the public key to an RSA Public Key file
  openssl rsa -in temp.out.pubkey.pem -pubin -RSAPublicKey_out -out $out_public_key_file

  # remove temporary file
  rm temp.out.pubkey.pem
}

create_self_signed_cert() {
  openssl req -new -x509 -key $PRIVATE_RSA_KEY_FILE -out $CERT_FILE -days 360  -subj "/C=$COUNTRY/ST=$STATE/L=$LOCALITY/O=$ORGNAME/CN=$COMMONNAME";
}

main() {
  # load config
  . config.sh

  check_openssl_installed;
  create_venv;
  mkdir -p $CERTDIR;
  create_rsa_pubkey_file $PRIVATE_RSA_KEY_FILE $PUBLIC_RSA_KEY_FILE

  if [ ! -f $CERT_FILE ]; then
    create_self_signed_cert;
  fi

  echo 'uploading certificate to Aruba InstantOn'
  python3 ./aruba-cert-uploader.py;
}

main


