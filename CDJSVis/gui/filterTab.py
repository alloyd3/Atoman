
"""
The filter tab for the main toolbar

@author: Chris Scott

"""
import os
import sys

from PyQt4 import QtGui, QtCore
import vtk
import numpy as np

from ..visutils.utilities import iconPath
from . import filterList
from ..rendering.text import vtkRenderWindowText
from ..visutils import utilities

try:
    from .. import resources
except ImportError:
    print "ERROR: could not import resources: ensure setup.py ran correctly"
    sys.exit(36)


################################################################################
class FilterTab(QtGui.QWidget):
    def __init__(self, parent, mainWindow, width):
        super(FilterTab, self).__init__(parent)
        
        self.mainToolbar = parent
        self.mainWindow = mainWindow
        self.toolbarWidth = width
        
        self.log = self.mainWindow.console.write
        
        self.filterListCount = 0
        self.filterLists = []
        self.onScreenInfo = {}
        self.onScreenInfoActors = vtk.vtkActor2DCollection()
        self.visAtomsList = []
        
        # layout
        filterTabLayout = QtGui.QVBoxLayout(self)
        filterTabLayout.setContentsMargins(0, 0, 0, 0)
        filterTabLayout.setSpacing(0)
        filterTabLayout.setAlignment(QtCore.Qt.AlignTop)
        
        row = QtGui.QWidget()
        rowLayout = QtGui.QHBoxLayout(row)
        rowLayout.setAlignment(QtCore.Qt.AlignTop)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setSpacing(0)
        
        #----- buttons for new/trash filter list
        runAll = QtGui.QPushButton(QtGui.QIcon(iconPath('view-refresh-all.svg')),'Apply lists')
        runAll.setStatusTip("Apply all filter lists")
        self.connect(runAll, QtCore.SIGNAL('clicked()'), self.runAllFilterLists)
        add = QtGui.QPushButton(QtGui.QIcon(iconPath('tab-new.svg')),'New list')
        add.setStatusTip("New filter list")
        self.connect(add, QtCore.SIGNAL('clicked()'), self.addFilterList)
        clear = QtGui.QPushButton(QtGui.QIcon(iconPath('edit-delete.svg')),'Clear lists')
        clear.setStatusTip("Clear all filter lists")
        self.connect(clear, QtCore.SIGNAL('clicked()'), self.clearAllFilterLists)
        
        rowLayout.addWidget(add)
        rowLayout.addWidget(clear)
        rowLayout.addWidget(runAll)
        
        filterTabLayout.addWidget(row)
        
        #----- add tab bar for filter lists
        self.filterTabBar = QtGui.QTabWidget(self)
        self.filterTabBar.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.connect(self.filterTabBar, QtCore.SIGNAL('currentChanged(int)'), self.filterTabBarChanged)
        filterTabLayout.addWidget(self.filterTabBar)
        
        # add a filter list
        self.addFilterList()
    
    def showFilterSummary(self):
        """
        Show filtering summary.
        
        """
        pass
    
    def removeOnScreenInfo(self):
        """
        Remove on screen info.
        
        """
        self.onScreenInfoActors.InitTraversal()
        actor = self.onScreenInfoActors.GetNextItem()
        while actor is not None:
            try:
                self.mainWindow.VTKRen.RemoveActor(actor)
            except:
                pass
            
            actor = self.onScreenInfoActors.GetNextItem()
        
        self.mainWindow.VTKWidget.ReInitialize()
        
        self.onScreenInfoActors = vtk.vtkActor2DCollection()
    
    def runAllFilterLists(self):
        """
        Run all the filter lists.
        
        """
        self.log("Running all filter lists")
        
        # first remove all old povray files
        os.system("rm -f %s/*.pov" % self.mainWindow.tmpDirectory)
        
        self.scalarBarAdded = False
        
        count = 0
        for filterList in self.filterLists:
            self.log("Running filter list %d" % (count,), 0, 1)
            
            if filterList.isStaticList():
                self.log("Static filter list: skipping", 0, 2)
            
            else:
                filterList.filterer.runFilters()
            
            count += 1
        
        self.refreshOnScreenInfo()
        
        self.mainWindow.setStatus("Ready")
    
    def refreshOnScreenInfo(self):
        """
        Refresh the on-screen information.
        
        """
        textSel = self.mainWindow.textSelector
        selectedText = textSel.selectedText
        textSettings = textSel.textSettings
        
        self.onScreenInfo = {}
        self.removeOnScreenInfo()
        
        if not selectedText.count():
            return
        
        # atom count doesn't change
        if "Atom count" not in self.onScreenInfo:
            self.onScreenInfo["Atom count"] = "%d atoms" % self.mainWindow.inputState.NAtoms
        
        # sim time doesn't change
        if "Simulation time" not in self.onScreenInfo:
            self.onScreenInfo["Simulation time"] = utilities.simulationTimeLine(self.mainWindow.inputState.simTime)
        
        # barrier doesn't change
        if "Energy barrier" not in self.onScreenInfo and self.mainWindow.inputState.barrier is not None:
            self.onScreenInfo["Energy barrier"] = "Barrier: %f eV" % self.mainWindow.inputState.barrier
        
        # visible counts always recalculated
        visCountActive = False
        visCount = 0
        for filterList in self.filterLists:
            if filterList.visible and not filterList.defectFilterSelected:
                visCountActive = True
                visCount += filterList.filterer.NVis
        
        if visCountActive:
            self.onScreenInfo["Visible count"] = "%d visible" % visCount
        
            visSpecCount = np.zeros(len(self.mainWindow.inputState.specieList), np.int32)
            for filterList in self.filterLists:
                if filterList.visible and not filterList.defectFilterSelected and filterList.filterer.NVis:
                    if len(visSpecCount) == len(filterList.filterer.visibleSpecieCount):
                        visSpecCount = np.add(visSpecCount, filterList.filterer.visibleSpecieCount)
        
            specieList = self.mainWindow.inputState.specieList
            self.onScreenInfo["Visible specie count"] = []
            for i, cnt in enumerate(visSpecCount):
                self.onScreenInfo["Visible specie count"].append("%d %s" % (cnt, specieList[i]))
        
        # defects counts
        defectFilterActive = False
        NVac = 0
        NInt = 0
        NAnt = 0
        showVacs = False
        showInts = False
        showAnts = False
        for filterList in self.filterLists:
            if filterList.visible and filterList.defectFilterSelected:
                defectFilterActive = True
                
                NVac += filterList.filterer.NVac
                NInt += filterList.filterer.NInt
                NAnt += filterList.filterer.NAnt
                
                # defects settings
                defectsSettings = filterList.currentSettings[0]
                
                if defectsSettings.showVacancies:
                    showVacs = True
                
                if defectsSettings.showInterstitials:
                    showInts = True
                
                if defectsSettings.showAntisites:
                    showAnts = True
        
        if defectFilterActive:
            # defect specie counters
            vacSpecCount = np.zeros(len(self.mainWindow.refState.specieList), np.int32)
            intSpecCount = np.zeros(len(self.mainWindow.inputState.specieList), np.int32)
            antSpecCount = np.zeros((len(self.mainWindow.refState.specieList), len(self.mainWindow.inputState.specieList)), np.int32)
            splitSpecCount = np.zeros((len(self.mainWindow.inputState.specieList), len(self.mainWindow.inputState.specieList)), np.int32)
            for filterList in self.filterLists:
                if filterList.visible and filterList.defectFilterSelected and filterList.filterer.NVis:
                    if len(vacSpecCount) == len(filterList.filterer.vacancySpecieCount):
                        vacSpecCount = np.add(vacSpecCount, filterList.filterer.vacancySpecieCount)
                        intSpecCount = np.add(intSpecCount, filterList.filterer.interstitialSpecieCount)
                        antSpecCount = np.add(antSpecCount, filterList.filterer.antisiteSpecieCount)
                        splitSpecCount = np.add(splitSpecCount, filterList.filterer.splitIntSpecieCount)
            
            # now add to dict
            self.onScreenInfo["Defect count"] = []
            
            if showVacs:
                self.onScreenInfo["Defect count"].append("%d vacancies" % (NVac,))
            
            if showInts:
                self.onScreenInfo["Defect count"].append("%d interstitials" % (NInt,))
            
            if showAnts:
                self.onScreenInfo["Defect count"].append("%d antisites" % (NAnt,))
            
            specListInput = self.mainWindow.inputState.specieList
            specListRef = self.mainWindow.refState.specieList
            specRGBInput = self.mainWindow.inputState.specieRGB
            specRGBRef = self.mainWindow.refState.specieRGB
            
            self.onScreenInfo["Defect specie count"] = []
            
            if showVacs:
                for i, cnt in enumerate(vacSpecCount):
                    self.onScreenInfo["Defect specie count"].append(["%d %s vacancies" % (cnt, specListRef[i]), specRGBRef[i]])
            
            if showInts:
                for i, cnt in enumerate(intSpecCount):
                    self.onScreenInfo["Defect specie count"].append(["%d %s interstitials" % (cnt, specListInput[i]), specRGBInput[i]])
                
                if defectsSettings.identifySplitInts:
                    for i in xrange(len(specListInput)):
                        for j in xrange(i, len(specListInput)):
                            if j == i:
                                N = splitSpecCount[i][j]
                                rgb = specRGBInput[i]
                            else:
                                N = splitSpecCount[i][j] + splitSpecCount[j][i]
                                rgb = (specRGBInput[i] + specRGBInput[j]) / 2.0
                            
                            self.onScreenInfo["Defect specie count"].append(["%d %s-%s split ints" % (N, specListInput[i], specListInput[j]), rgb])
            
            if showAnts:
                for i in xrange(len(specListRef)):
                    for j in xrange(len(specListInput)):
                        if i == j:
                            continue
                        self.onScreenInfo["Defect specie count"].append(["%d %s on %s antisites" % (antSpecCount[i][j], specListInput[j], specListRef[i]), specRGBRef[i]])
        
        # alignment/position stuff
        topyLeft = self.mainWindow.VTKWidget.height() - 5
        topxLeft = 5
        topyRight = self.mainWindow.VTKWidget.height() - 5
        topxRight = self.mainWindow.VTKWidget.width() - 220
        
        # loop over selected text
        for i in xrange(selectedText.count()):
            item = selectedText.item(i)
            item = str(item.text())
            settings = textSettings[item]
            
            try:
                line = self.onScreenInfo[item]
                
                if item == "Visible specie count":
                    for j, specline in enumerate(line):
                        r, g, b = self.mainWindow.inputState.specieRGB[j]
                        
                        if settings.textPosition == "Top left":
                            xpos = topxLeft
                            ypos = topyLeft
                        else:
                            xpos = topxRight
                            ypos = topyRight
                        
                        # add actor
                        actor = vtkRenderWindowText(specline, 20, xpos, ypos, r, g, b)
                        
                        if settings.textPosition == "Top left":
                            topyLeft -= 20
                        else:
                            topyRight -= 20
                        
                        self.onScreenInfoActors.AddItem(actor)
                
                elif item == "Defect count":
                    for specline in line:
                        r = g = b = 0
                        
                        if settings.textPosition == "Top left":
                            xpos = topxLeft
                            ypos = topyLeft
                        else:
                            xpos = topxRight
                            ypos = topyRight
                        
                        # add actor
                        actor = vtkRenderWindowText(specline, 20, xpos, ypos, r, g, b)
                        
                        if settings.textPosition == "Top left":
                            topyLeft -= 20
                        else:
                            topyRight -= 20
                        
                        self.onScreenInfoActors.AddItem(actor)
                
                elif item == "Defect specie count":
                    for array in line:
                        lineToAdd = array[0]
                        r, g, b = array[1]
                        
                        if settings.textPosition == "Top left":
                            xpos = topxLeft
                            ypos = topyLeft
                        else:
                            xpos = topxRight
                            ypos = topyRight
                        
                        # add actor
                        actor = vtkRenderWindowText(lineToAdd, 20, xpos, ypos, r, g, b)
                        
                        if settings.textPosition == "Top left":
                            topyLeft -= 20
                        else:
                            topyRight -= 20
                        
                        self.onScreenInfoActors.AddItem(actor)
                
                else:
                    r = g = b = 0
                    
                    if settings.textPosition == "Top left":
                        xpos = topxLeft
                        ypos = topyLeft
                    else:
                        xpos = topxRight
                        ypos = topyRight
                    
                    # add actor
                    actor = vtkRenderWindowText(line, 20, xpos, ypos, r, g, b)
                    
                    if settings.textPosition == "Top left":
                        topyLeft -= 20
                    else:
                        topyRight -= 20
                    
                    self.onScreenInfoActors.AddItem(actor)
            
            except KeyError:
                pass
#                print "WARNING: '%s' not in onScreenInfo dict" % item
        
        # add to render window
        self.onScreenInfoActors.InitTraversal()
        actor = self.onScreenInfoActors.GetNextItem()
        while actor is not None:
            try:
                self.mainWindow.VTKRen.AddActor(actor)
            except:
                pass
            
            actor = self.onScreenInfoActors.GetNextItem()
        
        self.mainWindow.VTKWidget.ReInitialize()
    
    def addFilterList(self):
        """
        Add a new filter list
        
        """
        # widget to hold filter list
        filterListWidget = QtGui.QWidget()
        filterListLayout = QtGui.QVBoxLayout(filterListWidget)
        filterListLayout.setContentsMargins(0, 0, 0, 0)
        
        # add list
        list1 = filterList.FilterList(self, self.mainToolbar, self.mainWindow, self.filterListCount, self.toolbarWidth)
        filterListLayout.addWidget(list1)
        self.filterLists.append(list1)
        self.visAtomsList.append([])
        
        # add to tab bar
        self.filterTabBar.addTab(filterListWidget, str(self.filterListCount))
        
        # select new tab
        self.filterTabBar.setCurrentIndex(self.filterListCount)
        
        self.filterListCount += 1
    
    def clearAllFilterLists(self):
        """
        Clear all the filter lists
        
        """
        self.log("Clearing all filter lists")
        for filterList in self.filterLists:
            filterList.clearList()
            self.removeFilterList()
        
    def filterTabBarChanged(self, val):
        # guess need to handle addition and removal of tabs here
        pass
    
    def removeFilterList(self):
        """
        Remove a filter list
        
        """
        if self.filterListCount <= 1:
            return
        
        currentList = self.filterTabBar.currentIndex()
        
        self.filterLists[currentList].clearList()
        
        for i in xrange(self.filterListCount):
            if i > currentList:
                self.filterTabBar.setTabText(i, str(i - 1))
        
        self.filterTabBar.removeTab(currentList)
        
        self.filterLists.pop(currentList)
        
        self.visAtomsList.pop(currentList)
        
        self.filterListCount -= 1
    
    def refreshAllFilters(self):
        """
        Refresh filter settings
        
        """
        self.log("Refreshing filters", 3)
        for filterList in self.filterLists:
            for filterSettings in filterList.currentSettings:
                filterSettings.refresh()
    
    def gatherVisibleAtoms(self):
        """
        Builds an array containing all (unique) visible atoms.
        
        """
        visibleAtomsFull = None
        for filterList in self.filterLists:
            visibleAtoms = filterList.filterer.visibleAtoms
            
            if visibleAtomsFull is None:
                visibleAtomsFull = visibleAtoms
            else:
                visibleAtomsFull = np.append(visibleAtomsFull, visibleAtoms)
        
        visibleAtomsFull = np.unique(visibleAtomsFull)
        
        return visibleAtomsFull
        
        

