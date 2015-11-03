# -*- coding: utf-8 -*-
"""
To import from the parent directory
"""
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import time
import pytest
from subprocess import Popen


@pytest.fixture(scope='session')
def api_server(request):
    sys.stdout.write('Establishing API Server...')
    proc = Popen(['python', 'app.py'])

    def teardown():
        sys.stdout.write('Tearing down the API Server...')
        proc.kill()
        sys.stdout.write('Fin!\n')

    request.addfinalizer(teardown)

    'Wait for server to be loaded.'
    time.sleep(10)
    sys.stdout.write('Fin!\n')
    return None
