import serial
import time
import argparse
from typing import Optional, List


class VirtualJTAGSerial:
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        """
        Inizializza la comunicazione seriale con il Virtual JTAG.

        Args:
            port: Porta seriale (es. 'COM3' su Windows o '/dev/ttyUSB0' su Linux)
            baudrate: Velocità di comunicazione
            timeout: Timeout in secondi
        """
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Chiude la connessione seriale."""
        if self.serial.is_open:
            self.serial.close()

    def write_data(self, data: int, width: int = 8) -> bool:
        """
        Scrive dati sul Virtual JTAG.

        Args:
            data: Dato da scrivere
            width: Numero di bit del dato (default 8)

        Returns:
            bool: True se la scrittura è avvenuta con successo
        """
        try:
            # Verifica che il dato sia nei limiti
            if data >= (1 << width):
                raise ValueError(f"Il dato è troppo grande per {width} bits")

            # Prepara il comando di scrittura
            cmd = bytes([data & 0xFF])
            self.serial.write(cmd)
            self.serial.flush()
            return True

        except Exception as e:
            print(f"Errore durante la scrittura: {e}")
            return False

    def read_data(self, width: int = 8) -> Optional[int]:
        """
        Legge dati dal Virtual JTAG.

        Args:
            width: Numero di bit da leggere (default 8)

        Returns:
            int: Dato letto, None se c'è un errore
        """
        try:
            data = self.serial.read(width // 8)
            if len(data) == 0:
                raise TimeoutError("Timeout durante la lettura")
            return int.from_bytes(data, byteorder='big')

        except Exception as e:
            print(f"Errore durante la lettura: {e}")
            return None

    def read_multiple(self, num_bytes: int) -> Optional[List[int]]:
        """
        Legge multiple bytes dal Virtual JTAG.

        Args:
            num_bytes: Numero di bytes da leggere

        Returns:
            List[int]: Lista di bytes letti, None se c'è un errore
        """
        try:
            data = self.serial.read(num_bytes)
            if len(data) != num_bytes:
                raise TimeoutError(f"Letti solo {len(data)} bytes su {num_bytes} richiesti")
            return list(data)

        except Exception as e:
            print(f"Errore durante la lettura multipla: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description='Comunicazione con Virtual JTAG via Seriale')
    parser.add_argument('--port', default="COM1", help='Porta seriale (es. COM3 o /dev/ttyUSB0)')
    parser.add_argument('--baudrate', type=int, default=115200, help='Baudrate (default: 115200)')
    parser.add_argument('--write', default=0, type=int, help='Dato da scrivere')
    parser.add_argument('--read', default=True, action='store_true', help='Leggi un byte')
    parser.add_argument('--read-multiple', type=int, help='Numero di bytes da leggere')

    args = parser.parse_args()

    try:
        with VirtualJTAGSerial(args.port, args.baudrate) as vjtag:
            if args.write is not None:
                success = vjtag.write_data(args.write)
                print(f"Scrittura {'completata' if success else 'fallita'}")

            if args.read:
                data = vjtag.read_data()
                if data is not None:
                    print(f"Dato letto: {data} (0x{data:02X})")

            if args.read_multiple:
                data = vjtag.read_multiple(args.read_multiple)
                if data is not None:
                    print("Dati letti:", ' '.join(f"0x{x:02X}" for x in data))

    except Exception as e:
        print(f"Errore: {e}")


if __name__ == "__main__":
    main()