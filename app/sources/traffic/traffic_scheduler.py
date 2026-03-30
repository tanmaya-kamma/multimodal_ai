import time
from traffic_source import run

INTERVAL = 60  #  1 minute for testing

print(" Starting traffic scheduler...")

while True:
    print("\n Running traffic ingestion...")

    try:
        run()
    except Exception as e:
        print(" Error:", e)

    print(f" Sleeping for {INTERVAL} seconds...\n")
    time.sleep(INTERVAL)