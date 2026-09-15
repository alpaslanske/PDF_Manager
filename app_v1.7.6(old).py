import json
from pathlib import Path
import sys
from collections import defaultdict

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QSplitter,
    QInputDialog,
    QTreeWidgetItem,
    QMenu,
    QMessageBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem
)
from PySide6.QtCore import Qt

from database import Database
#from widgets.pdf_viewer import PDFViewer
from widgets.pdf_viewer_scroll import PDFViewer
from widgets.bookmark_tree import BookmarkTree

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.db = Database()
        self.setWindowTitle("PDF Bookmark Manager V1")
        self.resize(1400, 900)

        self.viewer = PDFViewer()
        self.tree = BookmarkTree()
        self.page_label = QLabel("Sayfa: -/-")
        self.zoom_label = QLabel("Zoom: %150")

                # YENİ EKLEMENİZ GEREKEN BAĞLANTI (CONNECT) SATIRI:
        self.viewer.zoom_changed.connect(self.update_zoom_label)

        # Ayarlar dosyası yolu burada tanımlandı
        self.settings_file = Path("data/settings.json")

        self.setup_ui()
        self.load_groups()
        self.load_settings()

        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_tree_menu)
        self.tree.itemDoubleClicked.connect(self.open_bookmark)
        #self.zoom_label = QLabel("Zoom: %150")

    def setup_ui(self):
        central = QWidget()
        root = QVBoxLayout()
        toolbar = QHBoxLayout()

        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(4)

        btn_open = QPushButton("PDF Aç")
        btn_prev = QPushButton("←")
        btn_next = QPushButton("→")
        btn_zoom_in = QPushButton("+")
        btn_zoom_out = QPushButton("-")
        btn_group = QPushButton("Grup Ekle")
        btn_toggle = QPushButton("☰ Yer İmleri")

        btn_open.clicked.connect(self.open_pdf)
        btn_prev.clicked.connect(self.previous_page)
        btn_next.clicked.connect(self.next_page)
        btn_zoom_in.clicked.connect(self.zoom_in)
        btn_zoom_out.clicked.connect(self.zoom_out)
        btn_group.clicked.connect(self.add_group)
        btn_toggle.clicked.connect(self.toggle_bookmarks)

        btn_open.setMaximumHeight(28)
        btn_prev.setMaximumHeight(28)
        btn_next.setMaximumHeight(28)
        btn_zoom_in.setMaximumHeight(28)
        btn_zoom_out.setMaximumHeight(28)
        btn_group.setMaximumHeight(28)
        btn_toggle.setMaximumHeight(28)

        self.page_label.setMaximumHeight(28)
        self.zoom_label.setMaximumHeight(28)

        toolbar.addWidget(btn_open)
        toolbar.addWidget(btn_prev)
        toolbar.addWidget(btn_next)
        toolbar.addWidget(btn_zoom_in)
        toolbar.addWidget(btn_zoom_out)
        toolbar.addWidget(btn_group)
        toolbar.addWidget(btn_toggle)
        toolbar.addStretch()
        toolbar.addWidget(self.zoom_label)
        toolbar.addWidget(self.page_label)

        self.splitter = QSplitter()
        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.viewer)
        self.splitter.setSizes([250, 1150])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Ara...")
        self.search_box.textChanged.connect(self.filter_tree)

        #root.addWidget(self.search_box)
        #root.addLayout(toolbar)
        #root.addWidget(self.splitter)

        root.addLayout(toolbar)
        root.addWidget(self.search_box, 0)
        root.addWidget(self.splitter, 1)

        self.pdf_search = QLineEdit()
        self.pdf_search.returnPressed.connect(self.search_in_pdf)
        self.pdf_search.setPlaceholderText("PDF içinde ara...")

        btn_search = QPushButton("Bul")
        btn_search.clicked.connect(self.search_in_pdf)

        root.addWidget(self.pdf_search)
        root.addWidget(btn_search)

        self.search_results = QListWidget()
        self.search_results.setMaximumHeight(60)
        self.search_results.itemDoubleClicked.connect(
            self.goto_search_result
        )
        root.addWidget(self.search_results)

        central.setLayout(root)
        self.setCentralWidget(central)

    def open_pdf(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "PDF Aç", "", "PDF Files (*.pdf)"
        )
        if not filename:
            return
        self.current_pdf = filename
        self.viewer.open_pdf(filename)
        self.update_page_label()
        self.load_pdf_bookmarks()

    def load_pdf_bookmarks(self):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.text(0) == "📘 PDF Yer İmleri":
               self.tree.takeTopLevelItem(i)
               break

        if not self.viewer.doc:
            return

        toc = self.viewer.doc.get_toc()
        self.pdf_root = QTreeWidgetItem(["📘 PDF Yer İmleri"])
        self.tree.addTopLevelItem(self.pdf_root)
        parents = {0: self.pdf_root}

        for level, title, page in toc:
            item = QTreeWidgetItem([title])
            item.setData(0, Qt.UserRole + 100, page - 1)
            parent_item = parents[level - 1]
            parent_item.addChild(item)
            parents[level] = item
            self.pdf_root.setExpanded(True)

    def zoom_in(self):
        self.viewer.zoom_in()
        self.update_zoom_label()

    def zoom_out(self):
        self.viewer.zoom_out()
        self.update_zoom_label()

    def update_zoom_label(self):
        value = int(self.viewer.zoom * 100)
        self.zoom_label.setText(f"Zoom: %{value}")

    def next_page(self):
        self.viewer.next_page()
        self.update_page_label()

    def previous_page(self):
        self.viewer.previous_page()
        self.update_page_label()

    def update_page_label(self):
        if not self.viewer.doc:
            self.page_label.setText("Sayfa: -/-")
            return
        self.page_label.setText(
            f"Sayfa: {self.viewer.current_page + 1}/{len(self.viewer.doc)}"
        )

    def add_group(self):
        name, ok = QInputDialog.getText(self, "Yeni Grup", "Grup Adı")
        if not ok or not name.strip():
            return
        self.db.add_group(name.strip())
        self.load_groups()

    def load_groups(self):
        #self.load_settings()
        self.tree.clear()

        groups = self.db.get_groups()
        nodes = {}

        for gid, name, parent_id in groups:
            item = QTreeWidgetItem([name])
            item.setData(0, Qt.UserRole, gid)
            nodes[gid] = item

        for gid, name, parent_id in groups:
            item = nodes[gid]
            if parent_id and parent_id in nodes:
                nodes[parent_id].addChild(item)
            else:
                self.tree.addTopLevelItem(item)

        bookmarks = self.db.get_bookmarks()
        for bid, title, pdf_path, page, group_id in bookmarks:
            if group_id not in nodes:
                continue

            bookmark_item = QTreeWidgetItem([title])
            bookmark_item.setData(0, Qt.UserRole + 1, bid)
            nodes[group_id].addChild(bookmark_item)
        if self.viewer.doc:
            self.load_pdf_bookmarks()
        #print("load_groups sonrası:",self.viewer.current_page)

    def save_settings(self):
        data = {
            "window_width": self.width(),
            "window_height": self.height(),
            "splitter_sizes": self.splitter.sizes(),
            "last_pdf": getattr(self, "current_pdf", ""),
            "last_page": self.viewer.current_page,
            "bookmarks_visible": self.tree.isVisible()
        }
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_settings(self):
        if not self.settings_file.exists():
            return
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.resize(
                data.get("window_width", 1400),
                data.get("window_height", 900)
            )
            self.splitter.setSizes(
                data.get("splitter_sizes", [250, 1150])
            )

            pdf_path = data.get("last_pdf")
            page = data.get("last_page", 0)

            self.tree.setVisible(data.get("bookmarks_visible", True))

            if pdf_path and Path(pdf_path).exists():
                self.current_pdf = pdf_path
                self.viewer.open_pdf(pdf_path)
                self.viewer.goto_page(page)
                self.update_page_label()
        except Exception as e:
            print("Settings error:", e)

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def search_in_pdf(self):
        text = self.pdf_search.text().strip()
        if not text:
            return

        pages = self.viewer.search_text(text)
        grouped = defaultdict(int)
        for page, rect in pages:
            if page not in grouped:
                    grouped[page] = {
                    "count": 0,
                    "rect": rect
                    }

            grouped[page]["count"] += 1

        self.search_results.clear()
        total_matches = len(pages)
        self.search_results.addItem(
            f"{total_matches} eşleşme bulundu"
        )

        for page in sorted(grouped):
            count = grouped[page]["count"]
            rect = grouped[page]["rect"]

            item = QListWidgetItem(
                f"Sayfa {page + 1} ({count})"
            )

            item.setData(
                Qt.UserRole,
                (page, rect)
            )

            self.search_results.addItem(item)

    def goto_search_result(self, item):
        if item.data(Qt.UserRole) is None:
            return

        page, rect = item.data(Qt.UserRole)
        self.viewer.goto_page(page)
        self.viewer.set_highlight(rect)
        self.update_page_label()

    def toggle_bookmarks(self):
        self.tree.setVisible(not self.tree.isVisible())

    def filter_tree(self, text):
        text = text.lower().strip()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            self.filter_item(item, text)

    def filter_item(self, item, text):
        visible = text in item.text(0).lower()
        child_visible = False

        for i in range(item.childCount()):
            if self.filter_item(item.child(i), text):
                child_visible = True

        show = visible or child_visible or text == ""
        item.setHidden(not show)

        if child_visible and text != "":
            item.setExpanded(True)

        return show

    def show_tree_menu(self, pos):
        item = self.tree.itemAt(pos)
        menu = QMenu()

        add_bookmark = menu.addAction("Yer İmi Ekle")
        rename_bookmark = menu.addAction("Yer İmini Yeniden Adlandır")
        delete_bookmark = menu.addAction("Yer İmini Sil")
        add_subgroup = menu.addAction("Yeni Alt Grup")
        rename_group = menu.addAction("Grubu Yeniden Adlandır")
        delete_group = menu.addAction("Grubu Sil")

        action = menu.exec(self.tree.mapToGlobal(pos))

        if action == add_bookmark:
            self.add_bookmark(item)
        elif action == rename_bookmark:
            self.rename_bookmark(item)
        elif action == delete_bookmark:
            self.delete_bookmark(item)
        elif action == add_subgroup:
            self.add_subgroup(item)
        elif action == rename_group:
            self.rename_group(item)
        elif action == delete_group:
            self.delete_group_recursive(item)

    def add_bookmark(self, item):

        if not self.current_pdf or not item:
           return

        current_page = self.viewer.current_page

        group_id = item.data(0, Qt.UserRole)

        title, ok = QInputDialog.getText(
               self,
               "Yeni Yer İmi",
               "Yer İmi Adı"
        )

        if not ok or not title.strip():
           return

        self.db.add_bookmark(
            title.strip(),
            self.current_pdf,
            current_page,
            group_id
        )

        self.load_groups()

        self.viewer.goto_page(
            current_page
        )

        self.update_page_label()

    def delete_bookmark(self, item):
        if not item:
            return

        bookmark_id = item.data(0, Qt.UserRole + 1)
        if not bookmark_id:
            return

        self.db.delete_bookmark(bookmark_id)
        self.load_groups()

    def rename_bookmark(self, item):
        if not item:
            return

        bookmark_id = item.data(0, Qt.UserRole + 1)
        if not bookmark_id:
            return

        name, ok = QInputDialog.getText(
            self, "Yer İmi", "Yeni Ad", text=item.text(0)
        )

        if ok and name.strip():
            self.db.rename_bookmark(bookmark_id, name.strip())
            self.load_groups()

    def open_bookmark(self, item):
        pdf_page = item.data(0, Qt.UserRole + 100)

        if pdf_page is not None:
            self.viewer.goto_page(pdf_page)
            self.update_page_label()
            return

        bookmark_id = item.data(0, Qt.UserRole + 1)
        if not bookmark_id:
            return

        bookmark = self.db.get_bookmark(bookmark_id)
        if not bookmark:
            return

        pdf_path = bookmark[2]
        page = bookmark[3]

        self.current_pdf = pdf_path
        self.viewer.open_pdf(pdf_path)
        self.viewer.goto_page(page)
        self.update_page_label()

    def rename_group(self, item):
        if not item:
            return

        group_id = item.data(0, Qt.UserRole)
        if group_id is None:
            return

        name, ok = QInputDialog.getText(
            self,
            "Grubu Yeniden Adlandır",
            "Yeni Grup Adı",
            text=item.text(0)
        )

        if not ok or not name.strip():
            return

        self.db.rename_group(group_id, name.strip())
        self.load_groups()

    def delete_group_recursive(self, item):
        if not item:
            return

        group_id = item.data(0, Qt.UserRole)
        if group_id is None:
            return

        reply = QMessageBox.question(
            self,
            "Grup Sil",
            "Bu grup ve alt grupları silinsin mi?"
        )

        if reply != QMessageBox.Yes:
            return

        self._delete_group_children(item)
        self.db.delete_group(group_id)
        self.load_groups()

    def _delete_group_children(self, item):
        for i in range(item.childCount()):
            child = item.child(i)
            gid = child.data(0, Qt.UserRole)
            if gid:
                self._delete_group_children(child)
                self.db.delete_group(gid)

    def add_subgroup(self, item):
        if not item:
            return

        group_id = item.data(0, Qt.UserRole)
        if group_id is None:
            return

        name, ok = QInputDialog.getText(
            self, "Yeni Alt Grup", "Alt Grup Adı"
        )

        if not ok or not name.strip():
            return

        self.db.add_group(name.strip(), group_id)
        self.load_groups()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
