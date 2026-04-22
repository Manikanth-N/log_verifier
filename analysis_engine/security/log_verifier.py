"""Cryptographic log verifier - DGCA CS-UAS Part 3 Clause 7.1 compliant.

Implements Ed25519 with Blake2b for secure log verification.
No external dependencies - uses Python stdlib only.
"""

import struct
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


# Record layout constants
HEADER_SIZE = 64
CHUNK_MAGIC = 0x48434831   # "HCH1"
END_MAGIC = 0x534C4F47     # "SLOG"
CHUNK_RECORD_SIZE = 44
END_RECORD_SIZE = 101

ALGORITHM_SHA256 = 1
ALGORITHM_BLAKE2B = 2


@dataclass
class VerificationResult:
    """Result of log verification."""
    status: str  # 'pass', 'fail', 'unsigned'
    hash_chain_valid: bool = False
    signature_valid: bool = False
    device_bound: bool = False
    algorithm: Optional[str] = None
    error_message: Optional[str] = None
    chunks_verified: int = 0
    total_chunks: int = 0
    compliance_level: str = 'none'  # 'beginner', 'pro', 'certified'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status,
            'hash_chain_valid': self.hash_chain_valid,
            'signature_valid': self.signature_valid,
            'device_bound': self.device_bound,
            'algorithm': self.algorithm,
            'error_message': self.error_message,
            'chunks_verified': self.chunks_verified,
            'total_chunks': self.total_chunks,
            'compliance_level': self.compliance_level,
        }


class SecureLogVerifier:
    """Verify cryptographically secured ArduPilot logs."""
    
    def __init__(self):
        # Ed25519 curve parameters
        self._P = 2**255 - 19
        self._Q = 2**252 + 27742317777372353535851937790883648493
        self._d = -121665 * self._modinv(121666) % self._P
        self._Gy = 4 * self._modinv(5) % self._P
        self._Gx = self._recover_x(self._Gy, 0)
        self._G = (self._Gx, self._Gy, 1, self._Gx * self._Gy % self._P)
    
    def verify_log(self, log_path: str, pubkey_path: Optional[str] = None,
                  mode: str = 'pro') -> VerificationResult:
        """
        Verify a secure log file.
        
        Args:
            log_path: Path to .BIN log file
            pubkey_path: Path to public key file (required for 'certified' mode)
            mode: 'beginner', 'pro', or 'certified'
        
        Returns:
            VerificationResult with status and details
        """
        if mode == 'beginner':
            # No verification in beginner mode
            return VerificationResult(
                status='unsigned',
                compliance_level='beginner',
                error_message='Beginner mode - no verification performed'
            )
        
        if mode == 'pro':
            # Pro mode - no cryptographic verification
            return VerificationResult(
                status='unsigned',
                compliance_level='pro',
                error_message='Pro mode - cryptographic verification not enabled'
            )
        
        # Certified mode - full verification
        if not pubkey_path:
            return VerificationResult(
                status='fail',
                compliance_level='certified',
                error_message='Public key required for certified mode'
            )
        
        try:
            with open(log_path, 'rb') as f:
                log_data = f.read()
            
            with open(pubkey_path, 'rb') as f:
                pubkey = f.read()
            
            if len(pubkey) != 32:
                return VerificationResult(
                    status='fail',
                    compliance_level='certified',
                    error_message=f'Invalid public key size: {len(pubkey)} bytes (expected 32)'
                )
            
            return self._verify_secure_log(log_data, pubkey)
        
        except FileNotFoundError as e:
            return VerificationResult(
                status='fail',
                compliance_level='certified',
                error_message=f'File not found: {e}'
            )
        except Exception as e:
            return VerificationResult(
                status='fail',
                compliance_level='certified',
                error_message=f'Verification error: {e}'
            )
    
    def _verify_secure_log(self, data: bytes, pubkey: bytes) -> VerificationResult:
        """Internal method to verify secure log with all checks."""
        result = VerificationResult(status='fail', compliance_level='certified')
        
        if len(data) < HEADER_SIZE:
            result.error_message = 'File too small - missing header'
            return result
        
        # Step 1: Verify header
        header = data[:HEADER_SIZE]
        try:
            magic, version, algorithm = struct.unpack_from('<III', header, 0)
        except struct.error:
            result.error_message = 'Invalid header format'
            return result
        
        if magic != 0x414C4853:  # "SHLA" (Secure Hash Log ArduPilot)
            result.error_message = f'Invalid magic: 0x{magic:08X}'
            return result
        
        if algorithm not in [ALGORITHM_SHA256, ALGORITHM_BLAKE2B]:
            result.error_message = f'Unknown algorithm: {algorithm}'
            return result
        
        result.algorithm = 'Blake2b' if algorithm == ALGORITHM_BLAKE2B else 'SHA-256'
        
        # Step 2: Verify hash chain
        header_hash = self._header_hash(algorithm, header)
        pos = HEADER_SIZE
        chunk_count = 0
        verified_chunks = 0
        prev_hash = header_hash
        
        while pos < len(data):
            if len(data) - pos < 4:
                break
            
            record_magic = struct.unpack_from('<I', data, pos)[0]
            
            if record_magic == END_MAGIC:
                # End record found
                if len(data) - pos < END_RECORD_SIZE:
                    result.error_message = 'Truncated end record'
                    return result
                
                end_hash = data[pos+4:pos+36]
                sig_len = data[pos+36]
                signature = data[pos+37:pos+37+sig_len]
                
                # Verify final hash matches chain
                if end_hash != prev_hash:
                    result.error_message = 'Hash chain broken at end record'
                    result.chunks_verified = verified_chunks
                    result.total_chunks = chunk_count
                    return result
                
                result.hash_chain_valid = True
                result.chunks_verified = verified_chunks
                result.total_chunks = chunk_count
                
                # Verify Ed25519 signature
                if sig_len == 64:
                    msg = data[:pos+36]  # Everything before signature
                    sig_valid = self._ed25519_verify(pubkey, signature, msg)
                    result.signature_valid = sig_valid
                    result.device_bound = sig_valid
                    
                    if sig_valid:
                        result.status = 'pass'
                        result.error_message = None
                    else:
                        result.error_message = 'Invalid Ed25519 signature'
                else:
                    result.error_message = f'Invalid signature length: {sig_len}'
                
                return result
            
            elif record_magic == CHUNK_MAGIC:
                if len(data) - pos < CHUNK_RECORD_SIZE:
                    result.error_message = 'Truncated chunk record'
                    return result
                
                chunk_hash = data[pos+4:pos+36]
                chunk_size = struct.unpack_from('<I', data, pos+36)[0]
                chunk_count += 1
                
                if pos + CHUNK_RECORD_SIZE + chunk_size > len(data):
                    result.error_message = f'Chunk {chunk_count} extends beyond file'
                    return result
                
                # Verify chunk hash
                chunk_data = data[pos+CHUNK_RECORD_SIZE:pos+CHUNK_RECORD_SIZE+chunk_size]
                computed_hash = self._chain_hash(algorithm, chunk_data, prev_hash)
                
                if computed_hash != chunk_hash:
                    result.error_message = f'Hash mismatch at chunk {chunk_count}'
                    result.chunks_verified = verified_chunks
                    result.total_chunks = chunk_count
                    return result
                
                verified_chunks += 1
                prev_hash = chunk_hash
                pos += CHUNK_RECORD_SIZE + chunk_size
            else:
                result.error_message = f'Unknown record magic: 0x{record_magic:08X}'
                return result
        
        result.error_message = 'No end record found - log incomplete'
        result.chunks_verified = verified_chunks
        result.total_chunks = chunk_count
        return result
    
    def _chain_hash(self, algorithm: int, data: bytes, prev: bytes) -> bytes:
        """Compute chain hash."""
        if algorithm == ALGORITHM_SHA256:
            return hashlib.sha256(data + prev).digest()
        return hashlib.blake2b(data + prev, digest_size=32).digest()
    
    def _header_hash(self, algorithm: int, data: bytes) -> bytes:
        """Compute header hash."""
        if algorithm == ALGORITHM_SHA256:
            return hashlib.sha256(data).digest()
        return hashlib.blake2b(data, digest_size=32).digest()
    
    # Ed25519 implementation
    def _modinv(self, x):
        return pow(x, self._P - 2, self._P)
    
    def _recover_x(self, y, sign):
        x2 = (y*y - 1) * self._modinv(self._d*y*y + 1) % self._P
        x = pow(x2, (self._P + 3) // 8, self._P)
        if (x*x - x2) % self._P != 0:
            x = x * pow(2, (self._P - 1) // 4, self._P) % self._P
        if x % 2 != sign:
            x = self._P - x
        return x
    
    def _pt_add(self, A, B):
        a, b = (A[1]-A[0])*(B[1]-B[0]) % self._P, (A[1]+A[0])*(B[1]+B[0]) % self._P
        c, dd = 2*A[3]*B[3]*self._d % self._P, 2*A[2]*B[2] % self._P
        e, f, g, h = b-a, dd-c, dd+c, b+a
        return (e*f % self._P, g*h % self._P, f*g % self._P, e*h % self._P)
    
    def _pt_mul(self, s, P):
        R = None
        while s:
            if s & 1:
                R = self._pt_add(R, P) if R else P
            P = self._pt_add(P, P)
            s >>= 1
        return R
    
    def _compress(self, P):
        zi = self._modinv(P[2])
        x, y = P[0]*zi % self._P, P[1]*zi % self._P
        return int.to_bytes(y | ((x & 1) << 255), 32, "little")
    
    def _decompress(self, b):
        y = int.from_bytes(b, "little")
        s = y >> 255
        y &= ~(1 << 255)
        x = self._recover_x(y, s)
        return (x, y, 1, x*y % self._P)
    
    def _blake2b512(self, *parts):
        h = hashlib.blake2b(digest_size=64)
        for p in parts:
            h.update(p)
        return h.digest()
    
    def _ed25519_verify(self, pk32: bytes, sig64: bytes, msg: bytes) -> bool:
        """Verify Ed25519-Blake2b signature."""
        if len(sig64) != 64 or len(pk32) != 32:
            return False
        try:
            R = self._decompress(sig64[:32])
            A = self._decompress(pk32)
        except Exception:
            return False
        
        Rb = self._compress(R)
        k = int.from_bytes(self._blake2b512(Rb, pk32, msg), "little") % self._Q
        S = int.from_bytes(sig64[32:], "little")
        
        if S >= self._Q:
            return False
        
        lhs = self._compress(self._pt_mul(S, self._G))
        rhs = self._compress(self._pt_add(R, self._pt_mul(k, A)))
        return lhs == rhs
