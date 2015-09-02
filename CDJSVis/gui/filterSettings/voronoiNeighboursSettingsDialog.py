
"""
Contains GUI forms for the Voronoi neighbours filter.

"""
from . import base
from ...filtering.filters import voronoiNeighboursFilter


################################################################################
class VoronoiNeighboursSettingsDialog(base.GenericSettingsDialog):
    """
    Voronoi neighbours filter settings form.
    
    """
    def __init__(self, mainWindow, title, parent=None):
        super(VoronoiNeighboursSettingsDialog, self).__init__(title, parent)
        
        self.filterType = "Voronoi neighbours"
        self.addProvidedScalar("Voronoi neighbours")
        
        # settings
        self._settings = voronoiNeighboursFilter.VoronoiNeighboursFilterSettings()
        
        # filtering options
        self.addCheckBox("filteringEnabled", toolTip="Filter atoms by Voronoi neighbours", label="<b>Enable filtering</b>",
                         extraSlot=self.filteringToggled)
        
        self.minVoroNebsSpin = self.addSpinBox("minVoroNebs", minVal=0, maxVal=999, step=1, toolTip="Minimum number of Voronoi neighbours",
                                               label="Minimum", settingEnabled="filteringEnabled")
        
        self.maxVoroNebsSpin = self.addSpinBox("maxVoroNebs", minVal=0, maxVal=999, step=1, toolTip="Maximum number of Voronoi neighbours",
                                               label="Maximum", settingEnabled="filteringEnabled")
    
    def filteringToggled(self, enabled):
        """Filtering toggled."""
        print "ENABLED", enabled
        self.minVoroNebsSpin.setEnabled(enabled)
        self.maxVoroNebsSpin.setEnabled(enabled)
