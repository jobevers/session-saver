import argparse
import sys
import time

import driver


def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    try:
        firefox, proxy = driver.get_driver()
        while True:
            time.sleep(1)
    finally:
        proxy.process.terminate()
        proxy.process.wait()


if __name__ == '__main__':
    sys.exit(main())
