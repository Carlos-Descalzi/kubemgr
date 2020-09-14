from .view import View
from .list import ListView, ListModel
import os
from kubemgr.util import ansi


class FileItem:
    def __init__(self, parent, filename, isdir):
        self.parent = parent
        self.filename = filename
        self.isdir = isdir

    def __str__(self):
        return self.filename + ("/" if self.isdir else "")

    @property
    def path(self):
        return os.path.abspath(os.path.join(self.parent, self.filename))


class FileListModel(ListModel):
    def __init__(self, path, file_filter=None):
        self._path = os.path.abspath(path)
        self._file_filter = file_filter or self._default_filter
        self._items = []
        self.update()

    def set_path(self, path):
        self._path = path
        self.update()

    def _default_filter(self, path, filename):
        return True

    def get_path(self):
        return self._path

    path = property(get_path, set_path)

    def go_into(self, item):
        self._path = item.path
        self.update()

    def update(self):
        self._items = []
        if self._path != "/":
            self._items.append(FileItem(self._path, "..", True))

        self._items += [
            FileItem(self._path, fname, os.path.isdir(os.path.join(self._path, fname)))
            for fname in os.listdir(self._path)
            if self._valid_file(self._path, fname)
        ]

    def _valid_file(self, path, filename):
        return filename[0] != "." and (
            os.path.isdir(os.path.join(path, filename))
            or self._file_filter(path, filename)
        )

    def get_item_count(self):
        return len(self._items)

    def get_item(self, index):
        return self._items[index]


class FileListView(ListView):
    def __init__(self, model=None):
        super().__init__(model=model, selectable=True)
        self._current_index = 0

    def render_item(self, item, current, selected):
        width = self._rect.width

        buff = ansi.begin()

        if current:
            buff.underline()

        return str(buff.write(str(item)).reset())


class FileChooser(View):
    def __init__(self, rect=None, path=None, file_filter=None):
        super().__init__(rect)
        self._file_list_model = FileListModel(path or os.getcwd(), file_filter)
        self._file_list_view = FileListView(model=self._file_list_model)
        self._file_list_view.on_select.add(self._on_item_selected)
        self._on_file_selected = None

    def set_application(self, application):
        super().set_application(application)
        self._file_list_view.set_application(application)

    def contains(self, child):
        return self._file_list_view == child

    def _on_item_selected(self, source, item):
        if item.isdir:
            self._file_list_model.go_into(item)
            self._selected_index = -1
            self._current_index = 0
            self.update()
        elif not item.isdir:
            self._notify_file_selected(item.path)

    def on_key_press(self, input_key):
        self._file_list_view.on_key_press(input_key)

    def _notify_file_selected(self, path):
        self._on_file_selected(path)

    @property
    def on_file_selected(self):
        return self._on_file_selected

    def update(self):
        rect = self._rect.copy()
        rect.y += 2
        rect.height -= 3
        self._file_list_view.set_rect(rect)
        self._file_list_view.update()

        (
            ansi.begin()
            .gotoxy(self._rect.x, self._rect.y)
            .write(self.get_color("header.bg"))
            .write(self.get_color("header.fg"))
            .bold()
            .writefill("Select file", self._rect.width)
            .reset()
            .gotoxy(self._rect.x, self._rect.y + 1)
            .writefill(self._file_list_model.path, self._rect.width)
            .gotoxy(self._rect.x, self._rect.y + self._rect.height - 1)
            .write(self.get_color("footer.bg"))
            .write(self.get_color("footer.fg"))
            .writefill("Enter: select, Esc: Exit", self._rect.width)
            .reset()
        ).put()
