'''
Created on Feb 28, 2013

@author: jmht
'''

# python imports
import logging
import os
import sys
import unittest

# our imports
import mrbump_cmd

def generate_jobscripts(ensemble_pdbs, amoptd, job_time=86400, ensemble_options=None):
    """Write the MRBUMP shell scripts for all the ensembles.

    Args:
    ensemble_pdbs -- list of the ensembles, each a single pdb file
    amoptd -- dictionary with job options
    
    The split_mr option used here was added for running on the hartree
    wonder machine where job times were limited to 12 hours, but is left
    in in case it's of use elsewhere.
    """
    
    # Remember programs = also used for looping
    if amoptd['split_mr']: mrbump_programs = amoptd['mrbump_programs']
    
    job_scripts = []
    extra_options = {}
    for ensemble_pdb in ensemble_pdbs:
        
        # Get name from pdb path
        name = os.path.splitext(os.path.basename(ensemble_pdb))[0]
        if ensemble_options and name in ensemble_options: extra_options = ensemble_options[name]
        
        # May need to run MR separately
        if amoptd['split_mr']:
            # create multiple jobs
            for program in mrbump_programs:
                jname = "{0}_{1}".format(name, program)
                amoptd['mrbump_programs'] = [ program ]
                # HACK - molrep only runs on a single processor
                # Can't do this any more as any job < 16 can't run on the 12 hour queue
                #if program == "molrep":
                #    amoptd['nproc'] = 1
                script = write_jobscript(name = jname,
                                         pdb = ensemble_pdb,
                                         amoptd = amoptd,
                                         job_time = job_time,
                                         extra_options = extra_options
                                         )
                #amoptd['nproc'] = nproc
                job_scripts.append( script )
        else:
            # Just run as usual
            script = write_jobscript(name = name,
                                     pdb = ensemble_pdb,
                                     amoptd = amoptd,
                                     job_time = job_time,
                                     extra_options = extra_options
                                     )
            job_scripts.append(script)
            
    # Reset amoptd
    if amoptd['split_mr']: amoptd['mrbump_programs'] = mrbump_programs
            
    if not len(job_scripts):
        msg = "No job scripts created!"
        logging.critical(msg)
        raise RuntimeError, msg
    
    return job_scripts
        
def write_jobscript(name, pdb, amoptd, directory=None, job_time=86400, extra_options={}):
    """
    Create the script to run MrBump for this PDB.
    
    Args:
    name -- used to identify job and name the run script
    pdb -- the path to the pdb file for this job
    amoptd -- dictionary with job options
    directory -- directory to write script to - defaults to cwd
    
    Returns:
    path to the script
    
    There is an issue here as the code to add the parallel job submission
    script header is required here, so we create a ClusterRun object.
    Should think about a neater way to do this rather then split the parallel stuff
    across two modules.
    """
    if not directory: directory = os.getcwd()
        
    # First write mrbump keyword file
    keyword_file = os.path.join(directory,name+'.mrbump')
    key_dict = mrbump_cmd.keyword_dict(amoptd,extra_options=extra_options)
    keywords = mrbump_cmd.mrbump_keywords(key_dict, jobid=name, ensemble_pdb=pdb)
    with open(keyword_file,'w') as f: f.write(keywords)
        
    # Next the script to run mrbump
    ext='.bat' if sys.platform.startswith("win") else '.sh'
    script_path = os.path.join(directory,name+ext)
    with open(script_path, "w") as job_script:
        # Header
        if not sys.platform.startswith("win"):
            script_header = '#!/bin/sh\n'
            script_header += '[[ ! -d $CCP4_SCR ]] && mkdir $CCP4_SCR\n\n'
            job_script.write(script_header)
        
        # Get the mrbump command-line
        jobcmd = mrbump_cmd.mrbump_cmd(amoptd,name,keyword_file)
        job_script.write(jobcmd)
        
    # Make executable
    os.chmod(script_path, 0o777)
    
    return script_path

class Test(unittest.TestCase):

    def XtestLocal(self):
        
        import glob
        
        d = {
             'mtz' : '/opt/ample-dev1/examples/toxd-example/1dtx.mtz',
             'fasta' : '/opt/ample-dev1/examples/toxd-example/toxd_.fasta',
             'mrbump_programs' : ' molrep ',
             'use_buccaneer' : False ,
             'buccaneer_cycles' : 5,
             'use_arpwarp' : False,
             'arpwarp_cycles': 10,
             'use_shelxe' : True,
             'shelx_cycles' : 10,
             'FREE' : 'FreeR_flag',
             'F' : 'FP',
             'SIGF' : 'SIGFP',
             'nproc' : 3,
             'domain_all_chains_pdb' : None,
             'ASU': None,
             'mr_keys': [],
             'early_terminate' : False
             }
        
        ensemble_dir = "/home/Shared/ample-dev1/examples/toxd-example/ROSETTA_MR_0/ensembles_1"
        ensembles = []
        for infile in glob.glob( os.path.join( ensemble_dir, '*.pdb' ) ):
            ensembles.append(infile)
            
        mrbump_ensemble_local( ensembles, d )
            
    
    def XtestSuccess(self):
        
        pdbid = "/home/jmht/t/ample-dev1/examples/toxd-example/ROSETTA_MR_3/MRBUMP/cluster_2/search_All_atom_trunc_0.551637_rad_3_mrbump"
        
        self.assertTrue( check_success( pdbid ) )
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    #unittest.main()
    # Nothing here - see notes in worker
    pass
    
