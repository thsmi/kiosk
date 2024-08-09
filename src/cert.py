"""
Manages the certificate used to secure the web server.
"""
import subprocess
from pathlib import Path

class CertException(Exception):
    """
    Thrown in case something goes wrong in the certificate handling.
    """

class Cert():
    """
    Manages the certificate used to secure the https endpoint.
    """

    def __init__(self, root:str=None, key:str=None, cert:str=None):
        if not root:
            root = "/etc/kiosk/"
        self._root = Path(root).resolve()

        if not key:
            key = str(self._root / "key.pem")
        self._key = key

        if not cert:
            cert = str(self._root / "cert.pem")
        self._cert = cert

    def run(self, command, data, password=None):
        """
        Helper to simplify running open ssl commands.
        """
        if password is not None:
            command.extend(["-passin", "env:PASSWORD"])

        result = subprocess.run(
            command,
            input=data,
            text=False,
            capture_output=True,
            check=False,
            env={"PASSWORD": password})

        if result.returncode != 0:
            print("Error:", result.stderr.decode())
            raise CertException("Failed to retrieve cert")


    def update(self, pfx_data: bytes, cmd:str, target, password = None):
        """
        Updates the certificate with the given pfx container.
        """
        print(f"Updating {target} ...")

        self.run(
            ["openssl", "pkcs12", "-out", target, cmd, "-nodes"],
            pfx_data,
            password)

        print("... completed")

    def verify_pfx(self, pfx_data: bytes, password:str = None) -> bool:
        """
        Verifies if the pfx container is valid.
        """
        print("Verifying pfx container...")

        try:
            self.run(
                ['openssl', 'pkcs12', '-noout', '-info'],
                pfx_data,
                password)
        except Exception as ex:
            print(f"...failed with exception {ex}")
            return False

        return True


    def update_pfx(self, pfx_data, password = None):
        """
        Updates the certificates with a custom one.
        """

        if not self.verify_pfx(pfx_data, password):
            raise CertException("Invalid pfx container")

        self.update(pfx_data, "-nokey", self._cert, password)
        self.update(pfx_data, "-nocerts", self._key, password)


    def get_cert(self):
        """
        Gets the current certificate.
        """

        command = ["openssl", "x509", "-outform", "der", "-in", self._cert]

        result = subprocess.run(command, stdout=subprocess.PIPE, check=False)

        if result.returncode != 0:
            print("Error:", result.stderr.decode())
            raise CertException("Failed to retrieve cert")

        return result.stdout

    def clear(self):
        """
        Clears any stored certificates.
        """
        file_path = Path(self._cert)
        if file_path.exists():
            file_path.unlink()

        file_path = Path(self._key)
        if file_path.exists():
            file_path.unlink()

    def generate(self):
        """
        Generates a new self signed certificate.
        """
        subject = "/C=DE/ST=Baden-Wuerttemberg/L=Stuttgart"
        #=Organization/OU=Organizational Unit/CN=Common Name"

        command = [
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
            '-nodes', '-out', self._cert, '-keyout', self._key,
            '-days', str(20*365), '-subj', subject
        ]

        print('Generating SSL certificate...')
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

        if result.returncode != 0:
            print(result.stdout.decode())
            print(result.stderr.decode())

            raise CertException("Failed to generate certificate")

        print('SSL certificate generated successfully.')


    def get_ssl_context(self):
        """
        Returns the ssl context needed by flask.
        """
        if not Path(self._cert).exists() or not Path(self._key).exists():
            self.generate()

        return (self._cert, self._key)
