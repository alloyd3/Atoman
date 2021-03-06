
"""
Lattice module, with Lattice object and utilities

@author: Chris Scott

"""
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import division
import logging
import copy

import numpy as np

from .atoms import elements
from ..algebra import vectors
from . import _lattice
from . import _output
from six.moves import range


class Lattice(object):
    """
    The Lattice object.
    
    """
    def __init__(self):
        self.NAtoms = 0
        self.cellDims = np.array([100, 100, 100], np.float64)
        
        self.specieList = []
        self.specieCount = np.empty(0, np.int32)
        self.specieMass = np.empty(0, np.float64)
        self.specieCovalentRadius = np.empty(0, np.float64)
        self.specieRGB = np.empty((0, 3), np.float64)
        self.specieAtomicNumber = np.empty(0, np.int32)
        
        self.minPos = np.zeros(3, np.float64)
        self.maxPos = np.zeros(3, np.float64)
        
        self.atomID = np.empty(0, np.int32)
        self.specie = np.empty(0, np.int32)
        self.pos = np.empty(0, np.float64)
        self.charge = np.empty(0, np.float64)
        
        self.scalarsDict = {}
        self.scalarsFiles = {}
        self.vectorsDict = {}
        self.vectorsFiles = {}
        self.attributes = {}
        
        self.PBC = np.ones(3, np.int32)
    
    def wrapAtoms(self):
        """
        Wrap atoms that have left the periodic cell.
        
        """
        return _lattice.wrapAtoms(self.NAtoms, self.pos, self.cellDims, self.PBC)
    
    def atomSeparation(self, index1, index2, pbc):
        """
        Calculate the separation between two atoms.
        
        Parameters
        ----------
        index1, index2 : integer
            Indexes of the atoms you want to calculate the separation
            between.

        
        Returns
        -------
        atomSeparation : float
            The separation between the two atoms. This function will
            return 'None' if the indexes are out of range.
        
        Raises
        ------
        IndexError
            If the specified indexes are too large.
        
        """
        if index1 < self.NAtoms and index2 < self.NAtoms:
            atomSeparation = vectors.separation(self.atomPos(index1), self.atomPos(index2), self.cellDims, pbc)
        
        else:
            raise IndexError("Atom index(es) out of range: (%d or %d) >= %d" % (index1, index2, self.NAtoms))
        
        return atomSeparation
    
    def reset(self, NAtoms):
        """
        Reinitialise arrays and counters
        
        """
        self.NAtoms = NAtoms
        
        self.atomID = np.empty(NAtoms, np.int32)
        self.specie = np.empty(NAtoms, np.int32)
        self.pos = np.empty(3 * NAtoms, np.float64)
        self.charge = np.zeros(NAtoms, np.float64)
        
        self.specieList = []
        self.specieCount = np.empty(0, np.int32)
        self.specieMass = np.empty(0, np.float64)
        self.specieCovalentRadius = np.empty(0, np.float64)
        self.specieRGB = np.empty((0, 3), np.float64)
        self.specieAtomicNumber = np.empty(0, np.int32)
        
        self.minPos = np.zeros(3, np.float64)
        self.maxPos = np.zeros(3, np.float64)
         
        self.cellDims = np.zeros(3, np.float64)
        
        self.scalarsDict = {}
        self.scalarsFiles = {}
        self.vectorsDict = {}
        self.vectorsFiles = {}
        self.attributes = {}
        
        self.PBC = np.ones(3, np.int32)
    
    def calcTemperature(self, NMoving=None):
        """
        Calculate temperature in K
        
        """
        logger = logging.getLogger(__name__)
        logger.debug("Calculating temperature of Lattice")
        
        if "Kinetic energy" in self.scalarsDict:
            logger.debug("Got 'Kinetic energy' array from scalarsDict")
            ke = self.scalarsDict["Kinetic energy"]
        
        elif "KE" in self.scalarsDict:
            logger.debug("Got 'KE' array from scalarsDict")
            ke = self.scalarsDict["KE"]
        
        else:
            logger.debug("No kinetic energy information stored on Lattice")
            return None
        
        if NMoving is None:
            NMoving = self.NAtoms
        
        keSum = np.sum(ke)
        
        if keSum == 0:
            temperature = 0.0
        
        else:
            boltzmann = 8.6173324e-5
            temperature = 2.0 * keSum / (3.0 * boltzmann * NMoving)
        
        return temperature
    
    def density(self):
        """
        Return density of lattice
        
        """
        vol = self.volume()
        if vol == 0:
            return
        return self.NAtoms / vol
    
    def volume(self):
        """
        Return volume of lattice
        
        """
        return self.cellDims[0] * self.cellDims[1] * self.cellDims[2]
    
    def addSpecie(self, sym, count=None):
        """
        Add specie to specie list
        
        """
        if sym in self.specieList:
            if count is not None:
                specInd = self.specieIndex(sym)
                self.specieCount[specInd] = count
            return
        
        if count is None:
            count = 0
        
        self.specieList.append(sym)
        self.specieCount = np.append(self.specieCount, np.int32(count))
        self.specieMass = np.append(self.specieMass, elements.atomicMass(sym))
        self.specieCovalentRadius = np.append(self.specieCovalentRadius, elements.covalentRadius(sym))
        rgbtemp = elements.RGB(sym)
        rgbnew = np.empty((1, 3), np.float64)
        rgbnew[0][0] = rgbtemp[0]
        rgbnew[0][1] = rgbtemp[1]
        rgbnew[0][2] = rgbtemp[2]
        self.specieRGB = np.append(self.specieRGB, rgbnew, axis=0)
    
    def addAtom(self, sym, pos, charge, atomID=None, scalarVals={}, vectorVals={}):
        """
        Add an atom to the lattice
        
        """
        if sym not in self.specieList:
            self.addSpecie(sym)
        
        # atom ID
        if atomID is None:
            atomID = self.NAtoms
        
        specInd = self.getSpecieIndex(sym)
        
        self.specieCount[specInd] += 1
        
        pos = np.asarray(pos, dtype=np.float64)
        
        self.atomID = np.append(self.atomID, np.int32(atomID))
        self.specie = np.append(self.specie, np.int32(specInd))
        self.pos = np.append(self.pos, pos)
        self.charge = np.append(self.charge, np.float64(charge))
        
        # wrap positions
        
        # min/max pos!!??
        for i in range(3):
            self.minPos[i] = min(self.minPos[i], pos[i])
            self.maxPos[i] = max(self.maxPos[i], pos[i])
        
        self.NAtoms += 1
        
        logger = logging.getLogger(__name__)
        
        for scalarName in list(self.scalarsDict.keys()):
            if scalarName in scalarVals:
                newval = scalarVals[scalarName]
                self.scalarsDict[scalarName] = np.append(self.scalarsDict[scalarName], np.float64(newval))
            
            else:
                self.scalarsDict.pop(scalarName)
                logger.warning("Removing '%s' scalars from Lattice (addAtom)", scalarName)
        
        for vectorName in list(self.vectorsDict.keys()):
            newval = []
            if vectorName in vectorVals:
                newval = vectorVals[vectorName]
            
            if len(newval) == 3:
                self.vectorsDict[vectorName] = np.append(self.vectorsDict[vectorName], np.asarray(newval,
                                                         dtype=np.float64))
            
            else:
                self.vectorsDict.pop(vectorName)
                logger.warning("Removing '%s' vectors from Lattice (addAtom)", vectorName)
    
    def removeAtom(self, index):
        """
        Remove an atom
        
        """
        specInd = self.specie[index]
        self.atomID = np.delete(self.atomID, index)
        self.specie = np.delete(self.specie, index)
        self.pos = np.delete(self.pos, [3 * index, 3 * index + 1, 3 * index + 2])
        self.charge = np.delete(self.charge, index)
        self.NAtoms -= 1
        
        # modify specie list / counter if required
        self.specieCount[specInd] -= 1
        if self.specieCount[specInd] == 0:
            self.removeSpecie(specInd)
        
        for scalarName in list(self.scalarsDict.keys()):
            self.scalarsDict[scalarName] = np.delete(self.scalarsDict[scalarName], index)
        
        for vectorName in list(self.vectorsDict.keys()):
            self.vectorsDict[vectorName] = np.delete(self.vectorsDict[vectorName],
                                                     [3 * index, 3 * index + 1, 3 * index + 2])
    
    def removeSpecie(self, index):
        """
        Remove a specie from the specie list.
        
        """
        self.specieCount = np.delete(self.specieCount, index)
        self.specieList.pop(index)
        self.specieCovalentRadius = np.delete(self.specieCovalentRadius, index)
        self.specieMass = np.delete(self.specieMass, index)
#         self.specieMassAMU = np.delete(self.specieMassAMU, index)
        self.specieRGB = np.delete(self.specieRGB, index, axis=0)
        
        for i in range(self.NAtoms):
            if self.specie[i] > index:
                self.specie[i] -= 1
    
    def calcForce(self, forceConfig):
        """
        Calculate force on lattice.
        
        """
        pass
    
#         if type(forceConfig) is not forces.ForceConfig:
#             print "FORCE CONFIG WRONG TYPE"
#             return 113
#
#         return forces.calc_force(self, forceConfig)
    
    def atomPos(self, index):
        """
        Return pointer to atom position within pos array: [xpos, ypos, zpos].
        
        """
        atomPos = None
        if index < self.NAtoms:
            atomPos = self.pos[3 * index:3 * index + 3]
        
        return atomPos
    
    def atomSym(self, index):
        """
        Returns symbol of given atom.
        
        """
        atomSym = None
        if index < self.NAtoms:
            atomSym = self.specieList[self.specie[index]]
        
        return atomSym
    
    def getSpecieIndex(self, sym):
        """
        Return index of specie in specie list.
        
        """
        if sym not in self.specieList:
            raise ValueError("Species '%s' is not in the species list" % sym)
        
        index = None
        for i in range(len(self.specieList)):
            if self.specieList[i] == sym:
                index = i
                break
        
        return index
    
    def setDims(self, dimsarray):
        
        self.cellDims[0] = float(dimsarray[0])
        self.cellDims[1] = float(dimsarray[1])
        self.cellDims[2] = float(dimsarray[2])
    
    def refreshElementProperties(self):
        """
        Refresh element properties.
        
        """
        for i, sym in enumerate(self.specieList):
            self.specieMass[i] = elements.atomicMass(sym)
            self.specieCovalentRadius[i] = elements.covalentRadius(sym)
            self.specieAtomicNumber[i] = elements.atomicNumber(sym)
            rgbtemp = elements.RGB(sym)
            self.specieRGB[i][0] = rgbtemp[0]
            self.specieRGB[i][1] = rgbtemp[1]
            self.specieRGB[i][2] = rgbtemp[2]
    
    def toLKMC(self, storeEnergies=False):
        """
        Convert the Lattice to LKMC.Lattice.
        
        Returns None if cannot load LKMC.
        
        """
        # try to load LKMC
        try:
            from LKMC import Lattice
            from LKMC import Atoms
        except ImportError:
            lkmcLattice = None
        else:
            lkmcLattice = Lattice.Lattice(0, storeEnergies=storeEnergies)
            lkmcLattice.NAtoms = self.NAtoms
            lkmcLattice.pos = self.pos
            lkmcLattice.specie = self.specie
            lkmcLattice.specieList = self.specieList
            lkmcLattice.specieCount = self.specieCount
            lkmcLattice.charge = self.charge
            lkmcLattice.minPos = self.minPos
            lkmcLattice.maxPos = self.maxPos
            lkmcLattice.cellDims[0] = self.cellDims[0]
            lkmcLattice.cellDims[4] = self.cellDims[1]
            lkmcLattice.cellDims[8] = self.cellDims[2]
            lkmcLattice.force = np.empty(3 * self.NAtoms, np.float64)
            lkmcLattice.specieCovalentRadius = self.specieCovalentRadius
            lkmcLattice.specieRGB = self.specieRGB
            lkmcLattice.specieMass = np.empty(len(self.specieList), np.float64)
            lkmcLattice.specieMassAMU = np.empty(len(self.specieList), np.float64)
            for i, sym in enumerate(self.specieList):
                lkmcLattice.specieMass[i] = Atoms.atomicMass(sym)
                lkmcLattice.specieMassAMU[i] = Atoms.atomicMassAMU(sym)
    
    def writeLattice(self, filename, visibleAtoms=None):
        """
        Write the Lattice to the given file. If visibleAtoms is passed only write those atoms.
        
        """
        # full lattice or just visible atoms
        if visibleAtoms is None:
            writeFullLattice = 1
            visibleAtoms = np.empty(0, np.int32)
        else:
            writeFullLattice = 0
        
        # call C function to write Lattice
        _output.writeLattice(filename, visibleAtoms, self.cellDims, self.specieList, self.specie, self.pos, self.charge,
                             writeFullLattice)
    
    def clone(self, lattice):
        """
        Copy given lattice into this instance
        
        """
        if lattice.NAtoms != self.NAtoms:
            self.reset(lattice.NAtoms)
        
        NAtoms = lattice.NAtoms
        
        # copy dims
        self.cellDims[0] = lattice.cellDims[0]
        self.cellDims[1] = lattice.cellDims[1]
        self.cellDims[2] = lattice.cellDims[2]
        
        # specie stuff
        NSpecies = len(lattice.specieList)
        self.specieList = []
        self.specieCount = np.zeros(NSpecies, np.int32)
        self.specieMass = np.empty(NSpecies, np.float64)
        self.specieCovalentRadius = np.empty(NSpecies, np.float64)
        self.specieAtomicNumber = np.zeros(NSpecies, np.int32)
        self.specieRGB = np.empty((NSpecies, 3), np.float64)
        for i in range(NSpecies):
            self.specieList.append(lattice.specieList[i])
            self.specieCount[i] = lattice.specieCount[i]
            self.specieMass[i] = lattice.specieMass[i]
            self.specieCovalentRadius[i] = lattice.specieCovalentRadius[i]
            self.specieAtomicNumber[i] = lattice.specieAtomicNumber[i]
            for j in range(3):
                self.specieRGB[i][j] = lattice.specieRGB[i][j]
        
        # atom data
        self.atomID = np.empty(NAtoms, np.int32)
        self.specie = np.empty(NAtoms, np.int32)
        self.pos = np.empty(3 * NAtoms, np.float64)
        self.charge = np.empty(NAtoms, np.float64)
        for i in range(NAtoms):
            self.atomID[i] = lattice.atomID[i]
            self.specie[i] = lattice.specie[i]
            self.charge[i] = lattice.charge[i]
            for j in range(3):
                self.pos[3 * i + j] = lattice.pos[3 * i + j]
        
        self.minPos[0] = lattice.minPos[0]
        self.minPos[1] = lattice.minPos[1]
        self.minPos[2] = lattice.minPos[2]
        self.maxPos[0] = lattice.maxPos[0]
        self.maxPos[1] = lattice.maxPos[1]
        self.maxPos[2] = lattice.maxPos[2]
        
        self.scalarsDict = copy.deepcopy(lattice.scalarsDict)
        self.vectorsDict = copy.deepcopy(lattice.vectorsDict)
        self.scalarsFiles = copy.deepcopy(lattice.scalarsFiles)
        self.vectorsFiles = copy.deepcopy(lattice.vectorsFiles)
        self.attributes = copy.deepcopy(lattice.attributes)
        
        self.PBC = copy.deepcopy(lattice.PBC)
