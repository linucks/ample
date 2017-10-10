#!/usr/bin/env ccp4-python

import argparse
import cPickle
import logging
import os
import pyrvapi
import shutil
import sys

#from ample.util import ample_util
from ample.util.ample_util import I2DIR, amoptd_fix_path
from ample.util.pyrvapi_results import AmpleOutput
from ample.constants import AMPLE_PKL

logging.basicConfig()

# Get the path to program.xml
parser = argparse.ArgumentParser()
parser.add_argument('-ample_pkl')
parser.add_argument('-ccp4i2_xml')
parser.add_argument('-own_gui', default=False, action='store_true')
opt, _ = parser.parse_known_args()

opkl = '/opt/ample.git/ample_testing/from_existing_models/resultsd.pkl'

# Create working directory
work_dir = os.path.abspath(I2DIR)
os.mkdir(work_dir)

# Copy in amopt pkl
with open(opt.ample_pkl) as f: od = cPickle.load(f)

# update paths and copy across old files
amoptd_fix_path(od, newroot=work_dir, i2mock=True)

# Need to add these
od['work_dir'] = work_dir
od['ccp4i2_xml'] = opt.ccp4i2_xml

with open(os.path.join(work_dir,AMPLE_PKL), 'w') as w: cPickle.dump(od, w)

# Run gui and create jsrview files from dict
AR = AmpleOutput(od, own_gui=opt.own_gui)
AR.display_results(od)

#pyrvapi.rvapi_store_document2('jens.rvapi')
