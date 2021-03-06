import os
import subprocess
import time

import pytest
import requests

from intake.util_tests import ex


MIN_PORT = 7480
MAX_PORT = 7489
PORT = MIN_PORT


def ping_server(url, swallow_exception):
    try:
        r = requests.get(url)
    except Exception as e:
        if swallow_exception:
            return False
        else:
            raise e

    return r.status_code == 200


def pick_port():
    global PORT
    port = PORT
    if port == MAX_PORT:
        PORT = MIN_PORT
    else:
        PORT += 1

    return port


@pytest.fixture(scope="module")
def intake_server(request):
    # Catalog path comes from the test module
    catalog_path = request.module.TEST_CATALOG_PATH

    # Start a catalog server on nonstandard port
    port = pick_port()
    cmd = [ex, '-m', 'intake.cli.server', '--sys-exit-on-sigterm',
           '--port', str(port)]
    if isinstance(catalog_path, list):
        cmd.extend(catalog_path)
    else:
        cmd.append(catalog_path)

    env = dict(os.environ)
    env['INTAKE_TEST'] = 'server'

    try:
        p = subprocess.Popen(cmd, env=env)
        url = 'http://localhost:%d' % (port,)

        # wait for server to finish initalizing, but let the exception through
        # on last retry
        retries = 500
        while not ping_server(url, swallow_exception=(retries > 1)):
            time.sleep(0.1)
            retries -= 1

        yield url
    finally:
        p.terminate()
        p.wait()
