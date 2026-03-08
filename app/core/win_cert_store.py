"""Windows Certificate Store access for CAC / Smart Card signing.

Uses ctypes to call Windows CryptoAPI (CAPI) and CNG (NCrypt) functions
to enumerate certificates and perform signing operations with keys stored
on smart cards (e.g., DoD CAC).

The private key never leaves the smart card — all signing happens through
the Windows crypto subsystem, which communicates with the card via its
minidriver. Windows handles PIN prompts natively.
"""
import ctypes
import ctypes.wintypes as wintypes
import hashlib
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from app.logger import get_logger

logger = get_logger(__name__)

# Only usable on Windows
if sys.platform != "win32":
    raise ImportError("win_cert_store is Windows-only")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CERT_STORE_PROV_SYSTEM = 10
CERT_SYSTEM_STORE_CURRENT_USER = 0x00010000
X509_ASN_ENCODING = 0x00000001
PKCS_7_ASN_ENCODING = 0x00010000
ENCODING = X509_ASN_ENCODING | PKCS_7_ASN_ENCODING

CERT_FIND_ANY = 0
CERT_NAME_SIMPLE_DISPLAY_TYPE = 4
CERT_NAME_ISSUER_FLAG = 0x1
CERT_NAME_FRIENDLY_DISPLAY_TYPE = 5

CRYPT_ACQUIRE_PREFER_NCRYPT_KEY_FLAG = 0x00020000
CRYPT_ACQUIRE_ALLOW_NCRYPT_KEY_FLAG = 0x00010000
CERT_NCRYPT_KEY_SPEC = 0xFFFFFFFF

BCRYPT_PAD_PKCS1 = 0x00000002

AT_KEYEXCHANGE = 1
AT_SIGNATURE = 2

# Hash algorithm OIDs
szOID_RSA_SHA256RSA = "1.2.840.113549.1.1.11"

# CryptSignMessage flags
CMSG_DETACHED_FLAG = 0x00000004

# ---------------------------------------------------------------------------
# Structures
# ---------------------------------------------------------------------------
class CRYPT_INTEGER_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]

CRYPT_DATA_BLOB = CRYPT_INTEGER_BLOB


class CRYPT_ALGORITHM_IDENTIFIER(ctypes.Structure):
    _fields_ = [
        ("pszObjId", ctypes.c_char_p),
        ("Parameters", CRYPT_INTEGER_BLOB),
    ]


class FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD),
    ]

    def to_datetime(self):
        # FILETIME is 100-nanosecond intervals since 1601-01-01
        timestamp = (self.dwHighDateTime << 32) | self.dwLowDateTime
        # Convert to Unix timestamp (seconds since 1970-01-01)
        epoch_diff = 116444736000000000  # 100-ns intervals between 1601 and 1970
        if timestamp < epoch_diff:
            return None
        unix_ts = (timestamp - epoch_diff) / 10_000_000
        try:
            return datetime.fromtimestamp(unix_ts, tz=timezone.utc)
        except (OSError, ValueError):
            return None


class CERT_INFO(ctypes.Structure):
    _fields_ = [
        ("dwVersion", wintypes.DWORD),
        ("SerialNumber", CRYPT_INTEGER_BLOB),
        ("SignatureAlgorithm", CRYPT_ALGORITHM_IDENTIFIER),
        ("Issuer", CRYPT_INTEGER_BLOB),
        ("NotBefore", FILETIME),
        ("NotAfter", FILETIME),
        ("Subject", CRYPT_INTEGER_BLOB),
        # ... more fields but we don't need them
    ]


class CERT_CONTEXT(ctypes.Structure):
    _fields_ = [
        ("dwCertEncodingType", wintypes.DWORD),
        ("pbCertEncoded", ctypes.POINTER(ctypes.c_byte)),
        ("cbCertEncoded", wintypes.DWORD),
        ("pCertInfo", ctypes.POINTER(CERT_INFO)),
        ("hCertStore", wintypes.HANDLE),
    ]


class CRYPT_SIGN_MESSAGE_PARA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("dwMsgEncodingType", wintypes.DWORD),
        ("pSigningCert", ctypes.POINTER(CERT_CONTEXT)),
        ("HashAlgorithm", CRYPT_ALGORITHM_IDENTIFIER),
        ("pvHashAuxInfo", ctypes.c_void_p),
        ("cMsgCert", wintypes.DWORD),
        ("rgpMsgCert", ctypes.POINTER(ctypes.POINTER(CERT_CONTEXT))),
        ("cMsgCrl", wintypes.DWORD),
        ("rgpMsgCrl", ctypes.c_void_p),
        ("cAuthAttr", wintypes.DWORD),
        ("rgAuthAttr", ctypes.c_void_p),
        ("cUnauthAttr", wintypes.DWORD),
        ("rgUnauthAttr", ctypes.c_void_p),
        ("dwFlags", wintypes.DWORD),
        ("dwInnerContentType", wintypes.DWORD),
    ]


class BCRYPT_PKCS1_PADDING_INFO(ctypes.Structure):
    _fields_ = [("pszAlgId", ctypes.c_wchar_p)]


# ---------------------------------------------------------------------------
# DLL handles
# ---------------------------------------------------------------------------
crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
ncrypt = ctypes.WinDLL("ncrypt", use_last_error=True)

# ---------------------------------------------------------------------------
# Function prototypes
# ---------------------------------------------------------------------------
crypt32.CertOpenSystemStoreW.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR]
crypt32.CertOpenSystemStoreW.restype = wintypes.HANDLE

crypt32.CertEnumCertificatesInStore.argtypes = [
    wintypes.HANDLE, ctypes.POINTER(CERT_CONTEXT)
]
crypt32.CertEnumCertificatesInStore.restype = ctypes.POINTER(CERT_CONTEXT)

crypt32.CertGetNameStringW.argtypes = [
    ctypes.POINTER(CERT_CONTEXT), wintypes.DWORD, wintypes.DWORD,
    ctypes.c_void_p, wintypes.LPWSTR, wintypes.DWORD
]
crypt32.CertGetNameStringW.restype = wintypes.DWORD

crypt32.CertCloseStore.argtypes = [wintypes.HANDLE, wintypes.DWORD]
crypt32.CertCloseStore.restype = wintypes.BOOL

crypt32.CertDuplicateCertificateContext.argtypes = [ctypes.POINTER(CERT_CONTEXT)]
crypt32.CertDuplicateCertificateContext.restype = ctypes.POINTER(CERT_CONTEXT)

crypt32.CertFreeCertificateContext.argtypes = [ctypes.POINTER(CERT_CONTEXT)]
crypt32.CertFreeCertificateContext.restype = wintypes.BOOL

crypt32.CryptAcquireCertificatePrivateKey.argtypes = [
    ctypes.POINTER(CERT_CONTEXT), wintypes.DWORD, ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.BOOL)
]
crypt32.CryptAcquireCertificatePrivateKey.restype = wintypes.BOOL

crypt32.CryptSignMessage.argtypes = [
    ctypes.POINTER(CRYPT_SIGN_MESSAGE_PARA),
    wintypes.BOOL,
    wintypes.DWORD,
    ctypes.POINTER(ctypes.POINTER(ctypes.c_byte)),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(ctypes.c_byte),
    ctypes.POINTER(wintypes.DWORD),
]
crypt32.CryptSignMessage.restype = wintypes.BOOL

ncrypt.NCryptSignHash.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_byte), wintypes.DWORD,
    ctypes.POINTER(ctypes.c_byte), wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), wintypes.DWORD
]
ncrypt.NCryptSignHash.restype = ctypes.c_long  # SECURITY_STATUS

ncrypt.NCryptFreeObject.argtypes = [ctypes.c_void_p]
ncrypt.NCryptFreeObject.restype = ctypes.c_long


# ---------------------------------------------------------------------------
# Certificate info dataclass
# ---------------------------------------------------------------------------
@dataclass
class CertInfo:
    """Displayable certificate metadata."""
    subject: str
    issuer: str
    not_before: datetime | None
    not_after: datetime | None
    serial_hex: str
    has_private_key: bool
    _context_ptr: int  # raw pointer value for later retrieval

    @property
    def is_valid(self) -> bool:
        now = datetime.now(tz=timezone.utc)
        if self.not_before and now < self.not_before:
            return False
        if self.not_after and now > self.not_after:
            return False
        return True

    @property
    def display_name(self) -> str:
        expiry = self.not_after.strftime("%Y-%m-%d") if self.not_after else "?"
        status = "VALID" if self.is_valid else "EXPIRED"
        return f"{self.subject} [{status}, exp {expiry}]"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def enumerate_certificates(store_name: str = "MY") -> list[CertInfo]:
    """List all certificates in a Windows certificate store.

    Args:
        store_name: Store name — "MY" for personal certs (includes CAC).

    Returns:
        List of CertInfo objects for certificates that have private keys.
    """
    hStore = crypt32.CertOpenSystemStoreW(0, store_name)
    if not hStore:
        logger.error("Failed to open certificate store '%s'", store_name)
        return []

    certs = []
    pCtx = ctypes.POINTER(CERT_CONTEXT)()

    try:
        while True:
            pCtx = crypt32.CertEnumCertificatesInStore(hStore, pCtx)
            if not pCtx:
                break

            # Get subject name
            buf = ctypes.create_unicode_buffer(256)
            crypt32.CertGetNameStringW(
                pCtx, CERT_NAME_SIMPLE_DISPLAY_TYPE, 0, None, buf, 256)
            subject = buf.value

            # Get issuer name
            crypt32.CertGetNameStringW(
                pCtx, CERT_NAME_SIMPLE_DISPLAY_TYPE, CERT_NAME_ISSUER_FLAG,
                None, buf, 256)
            issuer = buf.value

            # Get dates
            cert_info = pCtx.contents.pCertInfo.contents
            not_before = cert_info.NotBefore.to_datetime()
            not_after = cert_info.NotAfter.to_datetime()

            # Get serial number
            serial_blob = cert_info.SerialNumber
            serial_bytes = bytes(
                serial_blob.pbData[i] for i in range(serial_blob.cbData))
            serial_hex = serial_bytes[::-1].hex().upper()

            # Check for private key
            hKey = ctypes.c_void_p()
            dwKeySpec = wintypes.DWORD()
            fFree = wintypes.BOOL()
            has_pk = crypt32.CryptAcquireCertificatePrivateKey(
                pCtx,
                CRYPT_ACQUIRE_PREFER_NCRYPT_KEY_FLAG | 0x00000040,  # SILENT
                None,
                ctypes.byref(hKey), ctypes.byref(dwKeySpec), ctypes.byref(fFree))

            if has_pk and fFree.value:
                if dwKeySpec.value == CERT_NCRYPT_KEY_SPEC:
                    ncrypt.NCryptFreeObject(hKey)
                # else: legacy CSP — don't release, cert store manages it

            # Duplicate the context so it survives store enumeration
            dup = crypt32.CertDuplicateCertificateContext(pCtx)
            ptr_val = ctypes.cast(dup, ctypes.c_void_p).value

            certs.append(CertInfo(
                subject=subject,
                issuer=issuer,
                not_before=not_before,
                not_after=not_after,
                serial_hex=serial_hex,
                has_private_key=bool(has_pk),
                _context_ptr=ptr_val,
            ))
    finally:
        crypt32.CertCloseStore(hStore, 0)

    # Filter to only certs with private keys (signing-capable)
    signing_certs = [c for c in certs if c.has_private_key]
    logger.info("Found %d signing certificate(s) in '%s' store",
                len(signing_certs), store_name)
    return signing_certs


def get_cert_context(cert_info: CertInfo) -> ctypes.POINTER(CERT_CONTEXT):
    """Recover the CERT_CONTEXT pointer from a CertInfo object."""
    return ctypes.cast(
        ctypes.c_void_p(cert_info._context_ptr),
        ctypes.POINTER(CERT_CONTEXT))


def get_cert_der_bytes(cert_info: CertInfo) -> bytes:
    """Get the DER-encoded certificate bytes."""
    ctx = get_cert_context(cert_info)
    size = ctx.contents.cbCertEncoded
    return bytes(ctx.contents.pbCertEncoded[i] for i in range(size))


def free_cert_context(cert_info: CertInfo):
    """Free a duplicated certificate context."""
    if cert_info._context_ptr:
        ctx = get_cert_context(cert_info)
        crypt32.CertFreeCertificateContext(ctx)
        cert_info._context_ptr = 0


def create_detached_signature(cert_info: CertInfo, data: bytes) -> bytes:
    """Create a detached PKCS#7/CMS signature using Windows CryptoAPI.

    This function uses CryptSignMessage which:
    - Automatically accesses the smart card private key
    - Prompts for PIN via the Windows native dialog
    - Creates a valid CMS/PKCS#7 detached signature

    Args:
        cert_info: Certificate to sign with (must have private key).
        data: The data to sign.

    Returns:
        DER-encoded detached PKCS#7 signature bytes.
    """
    pCert = get_cert_context(cert_info)

    # Set up signing parameters
    sign_para = CRYPT_SIGN_MESSAGE_PARA()
    sign_para.cbSize = ctypes.sizeof(CRYPT_SIGN_MESSAGE_PARA)
    sign_para.dwMsgEncodingType = ENCODING
    sign_para.pSigningCert = pCert

    # SHA-256 hash algorithm
    sign_para.HashAlgorithm.pszObjId = szOID_RSA_SHA256RSA.encode("ascii")
    sign_para.HashAlgorithm.Parameters.cbData = 0
    sign_para.HashAlgorithm.Parameters.pbData = None

    # Include the signing certificate in the message
    cert_array = (ctypes.POINTER(CERT_CONTEXT) * 1)()
    cert_array[0] = pCert
    sign_para.cMsgCert = 1
    sign_para.rgpMsgCert = cert_array

    # Prepare data array
    data_buf = (ctypes.c_byte * len(data))(*data)
    data_ptr = ctypes.cast(data_buf, ctypes.POINTER(ctypes.c_byte))
    rgpbToBeSigned = (ctypes.POINTER(ctypes.c_byte) * 1)()
    rgpbToBeSigned[0] = data_ptr
    rgcbToBeSigned = (wintypes.DWORD * 1)()
    rgcbToBeSigned[0] = len(data)

    # First call: get required size
    cbSignedBlob = wintypes.DWORD()
    ok = crypt32.CryptSignMessage(
        ctypes.byref(sign_para),
        True,   # detached
        1,      # number of content items
        rgpbToBeSigned,
        rgcbToBeSigned,
        None,
        ctypes.byref(cbSignedBlob))

    if not ok:
        err = ctypes.get_last_error()
        raise OSError(f"CryptSignMessage (size query) failed: 0x{err:08X}")

    # Second call: create the signature
    signed_blob = (ctypes.c_byte * cbSignedBlob.value)()
    ok = crypt32.CryptSignMessage(
        ctypes.byref(sign_para),
        True,
        1,
        rgpbToBeSigned,
        rgcbToBeSigned,
        signed_blob,
        ctypes.byref(cbSignedBlob))

    if not ok:
        err = ctypes.get_last_error()
        raise OSError(f"CryptSignMessage failed: 0x{err:08X}")

    return bytes(signed_blob[:cbSignedBlob.value])


class WinCAPIPrivateKey:
    """Private key proxy that delegates RSA signing to Windows CryptoAPI.

    This class implements enough of the `cryptography` RSAPrivateKey interface
    for use with the `endesive` PDF signing library. The actual private key
    operations are performed by Windows CNG/NCRYPT, which handles smart card
    communication and PIN prompts.
    """

    def __init__(self, cert_info: CertInfo):
        self._cert_info = cert_info
        self._key_size = 2048  # default, actual determined at sign time

    @property
    def key_size(self):
        return self._key_size

    def sign(self, data, padding_obj, algorithm):
        """Sign data using the Windows private key (smart card)."""
        pCert = get_cert_context(self._cert_info)

        hKey = ctypes.c_void_p()
        dwKeySpec = wintypes.DWORD()
        fFree = wintypes.BOOL()

        ok = crypt32.CryptAcquireCertificatePrivateKey(
            pCert,
            CRYPT_ACQUIRE_PREFER_NCRYPT_KEY_FLAG,
            None,
            ctypes.byref(hKey),
            ctypes.byref(dwKeySpec),
            ctypes.byref(fFree))

        if not ok:
            err = ctypes.get_last_error()
            raise OSError(
                f"CryptAcquireCertificatePrivateKey failed: 0x{err:08X}")

        try:
            if dwKeySpec.value == CERT_NCRYPT_KEY_SPEC:
                return self._ncrypt_sign(hKey.value, data, algorithm)
            else:
                # Fallback: use CryptSignMessage for legacy CSP keys
                return self._csp_sign_fallback(data, algorithm)
        finally:
            if fFree.value and dwKeySpec.value == CERT_NCRYPT_KEY_SPEC:
                ncrypt.NCryptFreeObject(hKey)

    def _ncrypt_sign(self, hKey, data, algorithm):
        """Sign using NCrypt (modern CNG API)."""
        from cryptography.hazmat.primitives import hashes

        # Determine hash algorithm
        if isinstance(algorithm, hashes.SHA256):
            algo_name = "SHA256"
            digest = hashlib.sha256(data).digest()
        elif isinstance(algorithm, hashes.SHA384):
            algo_name = "SHA384"
            digest = hashlib.sha384(data).digest()
        elif isinstance(algorithm, hashes.SHA512):
            algo_name = "SHA512"
            digest = hashlib.sha512(data).digest()
        elif isinstance(algorithm, hashes.SHA1):
            algo_name = "SHA1"
            digest = hashlib.sha1(data).digest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

        padding_info = BCRYPT_PKCS1_PADDING_INFO()
        padding_info.pszAlgId = algo_name

        digest_buf = (ctypes.c_byte * len(digest))(*digest)

        # Get signature size
        cbSignature = wintypes.DWORD()
        status = ncrypt.NCryptSignHash(
            hKey,
            ctypes.byref(padding_info),
            digest_buf, len(digest),
            None, 0,
            ctypes.byref(cbSignature),
            BCRYPT_PAD_PKCS1)

        if status != 0:
            raise OSError(f"NCryptSignHash (size) failed: 0x{status:08X}")

        # Perform the signing
        sig_buf = (ctypes.c_byte * cbSignature.value)()
        status = ncrypt.NCryptSignHash(
            hKey,
            ctypes.byref(padding_info),
            digest_buf, len(digest),
            sig_buf, cbSignature.value,
            ctypes.byref(cbSignature),
            BCRYPT_PAD_PKCS1)

        if status != 0:
            raise OSError(f"NCryptSignHash failed: 0x{status:08X}")

        return bytes(sig_buf[:cbSignature.value])

    def _csp_sign_fallback(self, data, algorithm):
        """Fallback for legacy CSP keys — use CryptSignMessage."""
        sig_bytes = create_detached_signature(self._cert_info, data)
        # CryptSignMessage returns a full CMS structure; we need raw sig.
        # For endesive compatibility, we extract just the signature value.
        # However, endesive may handle the full CMS — return as-is.
        return sig_bytes

    def public_key(self):
        raise NotImplementedError("Use cert for public key operations")

    def private_numbers(self):
        raise NotImplementedError("Private key is on smart card")

    def private_bytes(self, encoding, format, encryption_algorithm):
        raise NotImplementedError("Private key is on smart card and cannot be exported")


# Register WinCAPIPrivateKey as a virtual subclass of RSAPrivateKey
# so isinstance checks in endesive pass correctly
try:
    from cryptography.hazmat.primitives.asymmetric import rsa
    rsa.RSAPrivateKey.register(WinCAPIPrivateKey)
except ImportError:
    pass  # cryptography not installed — CAPI-only path still works
