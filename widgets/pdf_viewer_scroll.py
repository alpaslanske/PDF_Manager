import pymupdf
from PySide6.QtCore import Signal, Qt  # Sinyal kütüphanesini ekleyin
from PySide6.QtWidgets import (
    QLabel,
    QScrollArea
)

from PySide6.QtGui import (
    QPixmap,
    QImage
)

from PySide6.QtCore import Qt

class PDFViewer(QScrollArea):
            # Sınıfın en başında (metotların dışında) sinyali tanımlayın
    zoom_changed = Signal()

    def __init__(self):

        super().__init__()

        self.doc = None
        self.current_page = 0
        self.zoom = 1.5

        self.image_label = QLabel()

        self.image_label.setAlignment(
            Qt.AlignCenter
        )

        self.setWidget(
            self.image_label
        )

        self.setWidgetResizable(
            False
        )
        self.setAlignment(Qt.AlignCenter)  #Added Gemini

        self.dragging = False
        self.last_pos = None
        self.highlight_rect = None

    def open_pdf(self, pdf_path):

        self.doc = pymupdf.open(
            pdf_path
        )

        self.current_page = 0

        self.render_page()

    def render_page(self):
        page = self.doc[self.current_page]
        #self.page_links = page.get_links()
        self.page_links = page.get_links()

        if not self.doc:
            return

        page = self.doc[
            self.current_page
        ]

        matrix = pymupdf.Matrix(
            self.zoom,
            self.zoom
        )

        pix = page.get_pixmap(
            matrix=matrix
        )

        image = QImage(
            pix.samples,
            pix.width,
            pix.height,
            pix.stride,
            QImage.Format_RGB888
        )
        if self.highlight_rect:
            from PySide6.QtGui import (
                 QPainter,
                 QColor,
                 QPen
            )

            painter = QPainter(image)

            rect = self.highlight_rect

            x = int(rect.x0 * self.zoom)
            y = int(rect.y0 * self.zoom)

            w = int((rect.x1 - rect.x0) * self.zoom)
            h = int((rect.y1 - rect.y0) * self.zoom)

            painter.fillRect(
                x, y, w, h,
                QColor(255, 255, 0, 80)
            )

            painter.setPen(
                QPen(QColor(255, 0, 0), 2)
            )

            painter.drawRect(
                x, y, w, h
            )


            painter.end()
        self.image_label.setPixmap(
            QPixmap.fromImage(image)
        )

        self.image_label.resize(
            pix.width,
            pix.height
        )
    def set_highlight(self, rect):
        self.highlight_rect = rect
        self.render_page()

    def next_page(self):

        if (
            self.doc and
            self.current_page < len(self.doc) - 1
        ):

            self.current_page += 1

            self.render_page()

    def previous_page(self):

        if (
            self.doc and
            self.current_page > 0
        ):

            self.current_page -= 1

            self.render_page()

    def goto_page(self, page):

        if not self.doc:
            return

        if page < 0:
            return

        if page >= len(self.doc):
            return

        self.current_page = page

        self.render_page()

    def search_text(self, text):
        if not self.doc:
           return []

        results = []

        for page_no in range(len(self.doc)):

            page = self.doc[page_no]

            matches = page.search_for(text)

            for rect in matches:

                results.append((page_no,rect))

        return results

    def mousePressEvent(self, event):

        pdf_x = (
            event.position().x()
            + self.horizontalScrollBar().value()
        ) / self.zoom

        pdf_y = (
            event.position().y()
            + self.verticalScrollBar().value()
        ) / self.zoom


        for link in self.page_links:

            rect = link["from"]

            if (
                rect.x0 <= pdf_x <= rect.x1
                and
                rect.y0 <= pdf_y <= rect.y1
            ):

                target_page = link.get("page")

                if target_page is not None:

                    self.goto_page(target_page)
                    return

        if event.button() == Qt.LeftButton:

            self.dragging = True

            self.last_pos = event.position()

            self.setCursor(
                Qt.ClosedHandCursor
            )

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):

        if self.dragging and self.last_pos:
            delta = (
                 event.position()
                 - self.last_pos
            )

            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value()
                - int(delta.x())
            )

            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value()
                - int(delta.y())
            )

            self.last_pos = event.position()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):

        self.dragging = False
        self.last_pos = None
        self.setCursor(
             Qt.ArrowCursor
             )
        super().mouseReleaseEvent(event)

    def zoom_in(self):

        self.zoom += 0.2

        self.render_page()

    def zoom_out(self):

        self.zoom = max(
            0.4,
            self.zoom - 0.2
        )

        self.render_page()

    def wheelEvent(self, event):

        if event.modifiers() & Qt.ControlModifier:

           if event.angleDelta().y() > 0:
              self.zoom_in()
           else:
              self.zoom_out()
           self.zoom_changed.emit()
           event.accept()
           return

        self.verticalScrollBar().setValue(
            self.verticalScrollBar().value()
            - event.angleDelta().y()
        )


        event.accept()

        super().wheelEvent(event)
