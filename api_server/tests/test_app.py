# -*- coding: utf-8 -*-
"""
To import from the parent directory
"""
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import app


def test_get_prod_info():
    "For now, it just tests wthether exception is thrown or not."
    assert app.get_prod_info(6770325723)
