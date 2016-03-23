"""Test functions for util.workers_util"""

import glob
import os
import stat
import sys
import tempfile
import unittest

from ample.testing import constants
from ample.util import workers_util

@unittest.skipIf(sys.platform.startswith("win"), "cannot launch scripts on Windows")
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.thisd =  os.path.abspath( os.path.dirname( __file__ ) )
        cls.ample_dir = constants.AMPLE_DIR
        cls.tests_dir=os.path.join(cls.ample_dir,"testing")
        cls.testfiles_dir = os.path.join(cls.tests_dir,'testfiles')
     
    def makeJob(self, name):
        script = """#!/usr/bin/python
import sys,time
print "I am job: {0}"
time.sleep( 3 )
sys.exit(0)
""".format( name )
        f = tempfile.NamedTemporaryFile("w+b", prefix=name, suffix=".py", delete=False)
        f.write(script)
        f.close()
        os.chmod(f.name, stat.S_IRWXU)
        return f.name
    
    def test_jobServer(self):
        jobs = []
        for j in range(15):
            j = os.path.abspath("job_{0}".format(j))
            jobs.append(self.makeJob(j))
             
        js = workers_util.JobServer()
        js.setJobs(jobs)
        js.start(nproc=2, early_terminate=True, check_success=workers_util._check_success_test)
        
        for j in jobs: os.unlink(j)
        for l in glob.glob("job_*.log"): os.unlink(l)
        pass
    
if __name__ == "__main__":
    unittest.main()
