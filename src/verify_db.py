# verify_db.py
from core.database import SessionLocal
from models.wallet import Wallet
from models.position import Position
from models.metric import PositionMetric
from sqlalchemy.orm import joinedload

def inspect_database():
    db = SessionLocal()
    print("--- Verificando la base de datos ---")

    wallets = db.query(Wallet).all()
    print(f"\n[+] Wallets encontradas: {len(wallets)}")
    for wallet in wallets:
        print(f"  - ID: {wallet.id}, Dirección: {wallet.address}")

    # Usamos joinedload para cargar eficientemente las métricas relacionadas
    positions = db.query(Position).options(joinedload(Position.metrics)).all()
    print(f"\n[+] Posiciones encontradas: {len(positions)}")
    for pos in positions:
        print(f"  - Posición Token ID: {pos.token_id} (Wallet: {pos.wallet.address})")
        print(f"    Pool: {pos.token0_symbol}/{pos.token1_symbol}")
        print(f"    Métricas guardadas: {len(pos.metrics)}")
        for metric in pos.metrics:
            print(f"      -> Snapshot a las {metric.snapshot_at.strftime('%Y-%m-%d %H:%M:%S')}: En rango? {metric.is_in_range}, Precio: {metric.current_price}")

    db.close()

if __name__ == "__main__":
    inspect_database()