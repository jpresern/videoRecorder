import odml
from MetadataEntry import MetadataEntry

__author__ = 'Jan Grewe'
try:
    from PyQt5 import QtGui, QtCore, QtWidgets
except:
    print('Unfortunately, your system misses the PyQt5 packages.')
    quit()


class MetadataTab(QtWidgets.QWidget):
    """This class creates label-and-lineedit-combinations in the tabs and allows for feedback communication."""

    def __init__(self, section, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.parent = parent
        self.section = section.clone()
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)
        self.page_scroll = QtWidgets.QScrollArea()
        self.layout.addWidget(self.page_scroll)
        self.scroll_contents = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_contents)
        self.parent.addTab(self, self.section.type)
        self.name_entry = None
        self.entries = {}
        self.create_tab()

    def create_tab(self):
        self.entries.clear()
        self.name_entry = None
        self.scroll_contents.setLayout(self.scroll_layout)
        self.page_scroll.setWidgetResizable(False)
        self.populate_tab()
        self.page_scroll.setWidget(self.scroll_contents)

    def populate_tab(self):
        p = odml.Property("name", self.section.name)
        self.name_entry = MetadataEntry(p, self)
        self.scroll_layout.addWidget(self.name_entry)
        for p in self.section.properties:
            entry = MetadataEntry(p, self)
            self.entries[p.name] = entry
            self.scroll_layout.addWidget(entry)

    def metadata(self):
        s = odml.Section(self.name_entry.get_property().value.value, type=self.section.type)
        for e in list(self.entries.values()):
            s.append(e.get_property())
        return s
