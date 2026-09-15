from PySide6.QtWidgets import (
    QTreeWidget
)


class BookmarkTree(QTreeWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setHeaderLabel(
            "Yer İmleri"
        )

        self.setAlternatingRowColors(
            True
        )

        self.setAnimated(
            True
        )

        self.setUniformRowHeights(
            True
        )
