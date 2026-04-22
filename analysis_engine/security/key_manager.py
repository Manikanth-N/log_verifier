"""Public key management for device binding."""

import json
from pathlib import Path
from typing import Optional, Dict


class KeyManager:
    """Manage public keys for fleet devices."""
    
    def __init__(self, fleet_db_path: Optional[str] = None):
        self.fleet_db_path = fleet_db_path
        self.fleet_db: Dict[str, str] = {}
        if fleet_db_path:
            self.load_fleet_database()
    
    def load_fleet_database(self):
        """Load fleet database from JSON file.
        
        Format:
        {
            "SN-001": "/path/to/SN-001_public_key.dat",
            "SN-002": "/path/to/SN-002_public_key.dat"
        }
        """
        try:
            with open(self.fleet_db_path, 'r') as f:
                self.fleet_db = json.load(f)
        except FileNotFoundError:
            self.fleet_db = {}
        except json.JSONDecodeError:
            self.fleet_db = {}
    
    def get_public_key_path(self, serial_number: str) -> Optional[str]:
        """Get public key path for a vehicle serial number."""
        return self.fleet_db.get(serial_number)
    
    def add_vehicle(self, serial_number: str, pubkey_path: str):
        """Add a vehicle to the fleet database."""
        self.fleet_db[serial_number] = pubkey_path
        if self.fleet_db_path:
            self.save_fleet_database()
    
    def remove_vehicle(self, serial_number: str):
        """Remove a vehicle from the fleet database."""
        if serial_number in self.fleet_db:
            del self.fleet_db[serial_number]
            if self.fleet_db_path:
                self.save_fleet_database()
    
    def save_fleet_database(self):
        """Save fleet database to JSON file."""
        if not self.fleet_db_path:
            return
        
        try:
            with open(self.fleet_db_path, 'w') as f:
                json.dump(self.fleet_db, f, indent=2)
        except Exception as e:
            print(f"Failed to save fleet database: {e}")
    
    def list_vehicles(self) -> Dict[str, str]:
        """List all vehicles in the fleet."""
        return self.fleet_db.copy()
