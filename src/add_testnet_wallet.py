# add_testnet_wallet.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from core.database import SessionLocal
from models.wallet import Wallet

# Elige una de las wallets públicas encontradas
PUBLIC_WALLET_ADDRESS = "0x5C42A138a53238749822aA482e213217b5A6b738"

db = SessionLocal()

# Comprobar si la wallet ya existe
existing_wallet = db.query(Wallet).filter(Wallet.address.ilike(PUBLIC_WALLET_ADDRESS)).first()

if existing_wallet:
    print(f"La wallet {PUBLIC_WALLET_ADDRESS} ya existe en la base de datos.")
    # Opcional: asegurarse de que está activa
    if not existing_wallet.is_active:
        existing_wallet.is_active = True
        print("La wallet ha sido reactivada.")
else:
    new_wallet = Wallet(
        address=PUBLIC_WALLET_ADDRESS, 
        notes="Public Sepolia Testnet Wallet"
    )
    db.add(new_wallet)
    print(f"Wallet pública {PUBLIC_WALLET_ADDRESS} añadida a la base de datos.")

db.commit()
db.close()