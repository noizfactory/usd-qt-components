from __future__ import absolute_import

from pxr import Sdf, Usd
from Qt import QtCore, QtGui, QtWidgets
from usdqt.outliner import (OutlinerTreeView, OutlinerViewDelegate,
                            OutlinerStageModel)
from usdqt.layers import LayerTextViewDialog, SubLayerDialog

from typing import (Any, Dict, Iterable, Iterator, List, Optional,
                    Tuple, TypeVar, Union)


class UsdOutliner(QtWidgets.QDialog):
    # emitted with the new edit layer when the edit target is changed
    editTargetChanged = QtCore.Signal(Sdf.Layer)

    def __init__(self, stage, parent=None):
        '''
        Parameters
        ----------
        stage : Usd.Stage
        parent : Optional[QtGui.QWidget]
        '''
        assert isinstance(stage, Usd.Stage), 'A Stage instance is required'
        super(UsdOutliner, self).__init__(parent=parent)

        self.stage = stage
        self.dataModel = OutlinerStageModel(self.stage, parent=self)

        # Widget and other Qt setup
        self.setModal(False)
        self.UpdateTitle()

        self._menuBar = QtWidgets.QMenuBar(self)
        self.menus = {}  # type: Dict[str, QtWidgets.QMenu]
        self.AddMenu('file', '&File')
        self.AddMenu('tools', '&Tools')
        self.PopulateMenus()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        layout.addWidget(self._menuBar)
        view = OutlinerTreeView(self.dataModel, parent=self)
        delegate = OutlinerViewDelegate(self.stage.GetEditTarget().GetLayer(),
                                        parent=self)
        self.editTargetChanged.connect(delegate.SetActiveLayer)
        self.editTargetChanged.connect(self.dataModel.ActiveLayerChanged)
        view.setItemDelegate(delegate)
        layout.addWidget(view)

        view.setColumnWidth(0, 360)
        self.view = view

        self.resize(900, 600)

    @property
    def editTarget(self):
        return self.stage.GetEditTarget().GetLayer()

    def UpdateTitle(self, identifier=None):
        '''
        Parameters
        ----------
        identifier : Optional[str]
            If not provided, acquired from the curent edit target
        '''
        if not identifier:
            identifier = self.editTarget.identifier
        self.setWindowTitle('Outliner - %s' % identifier)

    def UpdateEditTarget(self, layer):
        '''
        Parameters
        ----------
        layer : Sdf.Layer
        '''
        self.stage.SetEditTarget(layer)
        self.editTargetChanged.emit(layer)
        self.UpdateTitle()

    def AddMenu(self, name, label=None):
        '''
        Parameters
        ----------
        name : str
            name of registered menu
        label : Optional[str]
            label to display in the menu bar

        Returns
        -------
        QtWidgets.QMenu
        '''
        if label is None:
            label = name
        menu = self._menuBar.addMenu(label)
        self.menus[name] = menu
        return menu

    def GetMenu(self, name):
        '''
        Get a named menu from the application's registered menus

        Parameters
        ----------
        name : str
            name of registered menu

        Returns
        -------
        Optional[QtWidgets.QMenu]
        '''
        return self.menus.get(name.lower())

    def _ShowEditTargetLayerText(self):
        # FIXME: only allow one window. per layer could be nice here?
        d = LayerTextViewDialog(self.stage.GetEditTarget().GetLayer(),
                                parent=self)
        d.layerEdited.connect(self.dataModel.ResetStage)
        d.refresh()
        d.show()

    def _ChangeEditTarget(self):
        # FIXME: only allow one window
        d = SubLayerDialog(self.stage, parent=self)
        d.editTargetChanged.connect(self.UpdateEditTarget)
        d.show()

    def PopulateMenus(self):
        toolsMenu = self.GetMenu('tools')
        a = toolsMenu.addAction('Show Current Layer Text')
        a.triggered.connect(self._ShowEditTargetLayerText)
        a = toolsMenu.addAction('Change Edit Target')
        a.triggered.connect(self._ChangeEditTarget)

    @classmethod
    def FromUsdFile(cls, usdFile, parent=None):
        with Usd.StageCacheContext(Usd.BlockStageCaches):
            stage = Usd.Stage.Open(usdFile, Usd.Stage.LoadNone)
            assert stage
            stage.SetEditTarget(stage.GetSessionLayer())
        return cls(stage, parent=parent)


if __name__ == '__main__':
    # simple test
    import sys

    app = QtWidgets.QApplication(sys.argv)

    usdFileArg = sys.argv[1]

    dialog = UsdOutliner.FromUsdFile(usdFileArg)
    dialog.show()
    dialog.exec_()
