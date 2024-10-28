#!/usr/bin/env python
# coding: utf-8
import os
import pathlib
import subprocess
import time
from dataclasses import dataclass
from typing import Iterable, List, Tuple

from selenium import webdriver
from tqdm.auto import tqdm


def get_binary():
    # TODO: work for linux and windows too
    return '/Applications/Firefox.app/Contents/MacOS/firefox'


@dataclass
class LaunchedMitmProxy:
    host: str
    port: int
    process: subprocess.Popen


def launch_mitmproxy():
    host = os.environ.get('MITM_PROXY_HOST', 'localhost')
    port = int(os.environ.get('MITM_PROXY_PORT', 8080))
    cmd = ['poetry', 'run', 'mitmweb', '--listen-host', host, '-p',  str(port), '-s' 'addon.py']
    p = subprocess.Popen(cmd)
    return LaunchedMitmProxy(host, port, p)



def get_driver(proxy: LaunchedMitmProxy=None) -> Tuple[webdriver.Firefox, LaunchedMitmProxy]:
    mitm_proxy = proxy or launch_mitmproxy()
    print(f'Using {mitm_proxy.host}:{mitm_proxy.port} as proxy')

    firefox_options = webdriver.FirefoxOptions()
    firefox_options.set_preference('network.proxy.type', 1)
    # Set the host/port.
    firefox_options.set_preference('network.proxy.http', mitm_proxy.host)
    firefox_options.set_preference('network.proxy.https_port', mitm_proxy.port)
    firefox_options.set_preference('network.proxy.ssl', mitm_proxy.host)
    firefox_options.set_preference('network.proxy.ssl_port', mitm_proxy.port)
    firefox_options.binary_location = get_binary()

    # Docs: https://selenium-python.readthedocs.io/api.html#module-selenium.webdriver.firefox.webdriver
    driver = webdriver.Firefox(options=firefox_options)
    return driver, mitm_proxy


@dataclass
class FlowTracker:
    latest_flow_dir: pathlib.Path = None
    last_flow: pathlib.Path = None

    def get_last_flow(self) -> Tuple[pathlib.Path, pathlib.Path]:
        all_flow_dirs = get_http_data_folders()
        if all_flow_dirs:
            self.latest_flow_dir = all_flow_dirs[-1]
            self.last_flow = sorted(self.latest_flow_dir.iterdir(), key=lambda p: p.stat().st_ctime)[-1]
        else:
            self.latest_flow_dir = None
            self.last_flow = None
        return self.latest_flow_dir, self.last_flow

    # checkpoint is a better name because `get` implies no side effects
    def checkpoint(self) -> Tuple[pathlib.Path, pathlib.Path]:
        return self.get_last_flow()

    def get_new_flows(self) -> Iterable[pathlib.Path]:
        yield from get_new_flows(self.latest_flow_dir, self.last_flow)


def get_http_data_folders() -> List[pathlib.Path]:
    # the glob makes sure we're getting a timestamped folder
    return sorted(pathlib.Path('http-data/').glob('[0-9]'*8))


def get_new_flows(latest_flow_dir, last_flow) -> Iterable[pathlib.Path]:
    for flow_dir in get_http_data_folders():
        if latest_flow_dir and (flow_dir.name < latest_flow_dir.name):
            continue
        for p in sorted(flow_dir.iterdir(), key=lambda p: p.stat().st_ctime):
            if not last_flow:
                yield p
            elif p.stat().st_ctime > last_flow.stat().st_ctime:
                yield p


# better: https://www.cloudbees.com/blog/get-selenium-to-wait-for-page-load
def wait(seconds, why):
    for _ in tqdm(range(seconds), desc=f'{why}...', leave=False):
        time.sleep(1)

