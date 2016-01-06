'''
Created on 29 Dec 2015

@author: jmht
'''
import argparse
import imp
import os
import shutil
import sys

# Our imports
from ample_util import SCRIPT_EXT, SCRIPT_HEADER
import workers

AMPLE_DIR = os.sep.join(os.path.abspath(os.path.dirname(__file__)).split(os.sep)[ :-1 ])

class AmpleException(Exception): pass

def clean(test_dict):
    for name in test_dict.keys():
        run_dir = test_dict[name]['directory']
        os.chdir(run_dir)
        print "Cleaning {0} in directory {1}".format(name, run_dir)
        work_dir = os.path.join(run_dir, name)
        if os.path.isdir(work_dir): shutil.rmtree(work_dir)
        logfile = work_dir + '.log'
        if os.path.isfile(logfile): os.unlink(logfile)  
        script = work_dir + SCRIPT_EXT
        if os.path.isfile(script): os.unlink(script)
        
def load_module(mod_name, paths):
    try:
        mfile, pathname, desc = imp.find_module(mod_name, paths)
    except ImportError as e:
        print "Cannot find module: {0} - {1}".format(mod_name,e)
        return None
    
    try:
        test_module = imp.load_module(mod_name, mfile, pathname, desc)
    except Exception as e:
        print "Cannot load module: {0} - {1}".format(mod_name,e)
        return None
    finally:
        mfile.close()
 
    return test_module

def parse_args(test_dict=None, extra_args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-clean', action='store_true', default=False,
                        help="Clean up all test files/directories")
    parser.add_argument('-nproc', type=int, default=1,
                        help="Number of processors to run on (1 per job)")
    parser.add_argument('-dry_run', action='store_true', default=False,
                        help="Don\'t actually run the jobs")
    parser.add_argument('-rosetta_dir',
                        help="Location of rosetta installation directory")
    parser.add_argument('-submit_cluster', action='store_true', default=False,
                        help="Submit to a cluster queueing system")
    
    args = parser.parse_args()
    if args.rosetta_dir and not os.path.isdir(args.rosetta_dir):
        print "Cannot find rosetta_dir: {0}".format(args.rosetta_dir)
        sys.exit(1)
    
    argd = vars(args)
    if test_dict:
        if args.clean:
            clean(test_dict)
        else:
            run(test_dict, extra_args=extra_args, **argd)
    else:
        return argd

def run(test_dict,
        nproc=1,
        submit_cluster=False,
        dry_run=False,
        clean_up=True,
        rosetta_dir=None,
        extra_args=None,
        **kw):

    if dry_run: clean_up=False

    # Create scripts and path to resultsd
    scripts = []
    owd = os.getcwd()
    for name in test_dict.keys():
        run_dir = test_dict[name]['directory']
        os.chdir(run_dir)
        work_dir = os.path.join(run_dir, name)
        args = test_dict[name]['args']
        # Rosetta is the only think likely to change between platforms so we update the entry
        if rosetta_dir and '-rosetta_dir' in args:
            args = update_args(args, ['-rosetta_dir', rosetta_dir])
        if extra_args:
            args = update_args(args, extra_args)
        script = write_script(work_dir,  args + ['-work_dir', work_dir])
        scripts.append(script)
        # Set path to the results pkl file we will use to run the tests
        test_dict[name]['resultsd'] = os.path.join(work_dir,'resultsd.pkl')
        if clean_up:
            if os.path.isdir(work_dir): shutil.rmtree(work_dir)
            logfile = work_dir + '.log'
            if os.path.isdir(logfile): os.unlink(logfile)
        
        # Back to where we started
        os.chdir(owd)
    
    # Run all the jobs
    nproc = nproc
    submit_cluster = submit_cluster
    submit_qtype = 'SGE'
    submit_array = True
    if not dry_run:
        workers.run_scripts(job_scripts=scripts,
                            monitor=None,
                            chdir=True,
                            nproc=nproc,
                            job_time=3600,
                            job_name='test',
                            submit_cluster=submit_cluster,
                            submit_qtype=submit_qtype,
                            submit_queue=None,
                            submit_array=submit_array,
                            submit_max_array=None)
    
    # Now run the tests
    for name in test_dict.keys():
        resultsd = test_dict[name]['resultsd']
        if not os.path.isfile(resultsd):
            print "**** Job \'{0}\' did not generate a pkl file: {1}".format(name, resultsd)
            continue
        try:
            # Get path to pickled results file and pass it to the test function
            test_dict[name]['test'](resultsd)
            print "Job \'{0}\' succeeded".format(name)
        except AmpleException as ae:
            print "* Job \'{0}\' failed a test: {1}".format(name, ae)
        except Exception as e:
            print "*** Job \'{0}\' generated an exception: {1}".format(name, e)


def write_script(path, args):
    """Write script - ARGS MUST BE IN PAIRS"""
    ample = os.path.join(AMPLE_DIR,'bin', 'ample.py')
    script = path + SCRIPT_EXT
    with open(script, 'w') as f:
        f.write(SCRIPT_HEADER + os.linesep)
        f.write(os.linesep)
        f.write(ample + " \\" + os.linesep)
        # Assumption is all arguments are in pairs
        arg_list = [ " ".join(args[i:i+2]) for i in range(0, len(args), 2) ]
        f.write(" \\\n".join(arg_list))
        f.write(os.linesep)
        f.write(os.linesep)
    
    os.chmod(script, 0o777)
    return os.path.abspath(script)

def update_args(args, new_args):
    """Add/update any args - MUST BE IN PAIRS!"""
    for i in range(0, len(new_args), 2):
        if new_args[i] not in args:
            args += new_args[i:i+2]
        else:
            j = args.index(new_args[i])
            args[j+1] = new_args[i+1]
    return args   
    
