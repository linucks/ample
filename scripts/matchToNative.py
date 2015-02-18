#!/usr/bin/env ccp4-python

import os
import sys

root = os.sep.join( os.path.abspath(__file__).split( os.sep )[:-2] )
sys.path.insert( 0, os.path.join( root, "python" ) )
sys.path.insert( 0, os.path.join( root, "scripts" ) )

# We use MRBUMP's MTZ_parse
sys.path.append(os.path.join(os.environ["CCP4"], "share", "mrbump", "include", "file_info")) # For MTZ_parse

import ample_util
import csymmatch
import phenixer
import MTZ_parse

def run( nativePdb, nativeMtz=None, nativeMap=None, mrPdbs=None, outDir=None ):

    # Find out where we're running from
    if outDir is not None:
        if not os.path.isdir(outDir):
            raise RuntimeError,"Cannot find output directory: {0}".format(outDir)
        outDir=os.path.abspath(outDir)
    else:
        outDir=os.getcwd()
        
    if nativeMap is None:
        nativeMap = generateMap(nativePdb,nativeMtz)
    
    if not os.path.isfile(nativeMap):
        raise RuntimeError,"Cannot find nativeMap: {0}".format(nativeMap)
        
    
    for mrPdb in mrPdbs:
        print "Searching for origin shift using: {0} {1}".format( nativeMap, mrPdb )
        origin =  phenixer.ccmtzOrigin( nativeMap, mrPdb )
        
        # offset.pdb is the mrPdb moved onto the new origin
        offsetPdb = "offset.pdb"
        print "Found origin: {0}\nOffset pdb is: {1}".format( origin, offsetPdb )
        
        # Run csymmatch to map offsetted pdb onto native
        csymmPdb = ample_util.filename_append( filename=mrPdb, astr="csymmatch", directory=outDir )
        print "Running csymmatch to wrap {0} onto native {1}".format( offsetPdb, nativePdb )
        csymmatch.Csymmatch().run( refPdb=nativePdb, inPdb=offsetPdb, outPdb=csymmPdb, originHand=False )
        
        print "Matched PDB is: {0}".format( csymmPdb )
    
    return

def generateMap(nativePdb,nativeMtz):
    
    # Get the labels from the MTZ file
    print "Parsing MTZ file {0} to determine column labels".format( nativeMtz )
    mtzp = MTZ_parse.MTZ_parse()
    mtzp.run_mtzdmp( nativeMtz )
    # Generate map from 
    print "Generating map from: {0} {1}".format( nativeMtz,
                                                 nativePdb )
    return phenixer.generateMap( nativeMtz,
                                   nativePdb,
                                   FP= mtzp.F,
                                   SIGFP=mtzp.SIGF,
                                   FREE=mtzp.FreeR_flag,
                                  )

if __name__ == "__main__":
    assert len(sys.argv) >= 4,"Usage: {0} native.pdb native.mtz molecular_replacement.pdb[s]".format( sys.argv[0] )
    nativePdb = sys.argv[1]
    nativeMtz = sys.argv[2]
    mrPdbs    = sys.argv[3:]
    run( nativePdb, nativeMtz, mrPdbs )
