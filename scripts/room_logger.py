"""Record TMP36 readings streamed by the Arduino over serial to a CSV file.

The Arduino sends one line per sample: ``time_ms,raw,voltage,temp_C``.
Lines that do not match this format (start-up messages, partial lines)
are skipped.

    python scripts/room_logger.py --port COM3 --out room_unfiltered.csv

Requires pyserial (``pip install pyserial``).
"""
import argparse
import csv
import time


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--port", default="COM3", help="serial port of the Arduino")
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--samples", type=int, default=3273, help="number of samples to record")
    ap.add_argument("--out", default="room_log.csv", help="output CSV file")
    args = ap.parse_args()

    import serial

    ser = serial.Serial(args.port, args.baud, timeout=1)
    time.sleep(2)  # the board resets when the port opens

    count = 0
    with open(args.out, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["time_ms", "raw", "voltage", "temp_C"])
        print(f"Recording {args.samples} samples to {args.out} ...")

        while count < args.samples:
            line = ser.readline().decode(errors="ignore").strip()
            parts = line.split(",")
            if len(parts) == 4 and parts[0].isdigit():
                writer.writerow(parts)
                file.flush()
                print(line)
                count += 1

    ser.close()
    print(f"Finished. Saved {args.out}")


if __name__ == "__main__":
    main()
