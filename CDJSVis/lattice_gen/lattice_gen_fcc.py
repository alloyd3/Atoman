
"""
Generate FCC lattice

@author: Chris Scott

"""
from ..state.lattice import Lattice


################################################################################

class Args(object):
    """
    NCells: 3-tuple containing number of unit cells in each direction (default=(10,10,10))
    percGa: atomic percent Ga (max 25) (default=5)
    a0: lattice constant (default=4.64)
    f: output filename
    x,y,z: PBCs in each direction (default=True)
    quiet: suppress stdout
    
    """
    def __init__(self, sym="Au", NCells=[10,10,10], a0=4.078, pbcx=True, pbcy=True, pbcz=True, quiet=False):
        self.sym = sym
        self.NCells = NCells
        self.a0 = a0
        self.pbcx = pbcx
        self.pbcy = pbcy
        self.pbcz = pbcz
        self.quiet = quiet

################################################################################

class FCCLatticeGenerator(object):
    """
    FCC lattice generator.
    
    """
    def __init__(self, log=None):
        self.logger = log
    
    def log(self, message, level=0, indent=0):
        """
        Write log message.
        
        """
        if self.logger is not None:
            self.logger(message, level=level, indent=indent)
    
    def generateLattice(self, args):
        """
        Generate the lattice.
        
        """
        if not args.quiet:
            self.log("Generating FCC lattice")
        
        # lattice constants
        a0 = args.a0
        a1 = a0 / 2.0
        
        # define primitive cell (4 atoms)
        # corner atom is Ga
        UC_rx = [0.0, 0.0, a1,  a1]
        UC_ry = [0.0, a1,  0.0, a1]
        UC_rz = [0.0, a1,  a1,  0.0]
        
        # handle PBCs
        if args.pbcx:
            iStop = args.NCells[0]
        else:
            iStop = args.NCells[0] + 1
        
        if args.pbcy:
            jStop = args.NCells[1]
        else:
            jStop = args.NCells[1] + 1
        
        if args.pbcz:
            kStop = args.NCells[2]
        else:
            kStop = args.NCells[2] + 1
        
        # lattice dimensions
        dims = [a0*args.NCells[0], a0*args.NCells[1], a0*args.NCells[2]]
        
        # lattice structure
        lattice = Lattice()
        
        # set dimensions
        lattice.setDims(dims)
        
        # generate lattice
        count = 0
        for i in xrange(iStop):
            for j in xrange(jStop):
                for k in xrange(kStop):
                    for l in xrange(4):
                        # position of new atom
                        rx_tmp = UC_rx[l] + i * a0
                        ry_tmp = UC_ry[l] + j * a0
                        rz_tmp = UC_rz[l] + k * a0
                        
                        # skip if outside lattice (ie when making extra cell to get surface for non-periodic boundaries)
                        if (rx_tmp > dims[0]+0.0001) or (ry_tmp > dims[1]+0.0001) or (rz_tmp > dims[2]+0.0001):
                            continue
                        
                        # add to lattice structure
                        lattice.addAtom(args.sym, (rx_tmp, ry_tmp, rz_tmp), 0.0)
                        
                        count += 1
        
        NAtoms = count
        
        assert NAtoms == lattice.NAtoms
        
        if not args.quiet:
            self.log("Number of atoms: %d" % (NAtoms,), indent=1)
            self.log("Dimensions: %s" % (str(dims),), indent=1)
        
        return 0, lattice
