from contextvars import Context, ContextVar, copy_context
from functools import partial
from logging import Filter, LogRecord

file_prefix_var: ContextVar[str] = ContextVar("file prefix")
folder_name_var: ContextVar[str] = ContextVar("folder name")


class FilterByContext(Filter):
    def __init__(self, name: str, folder_name: str, file_prefix: str):
        super().__init__(name)
        self.folder_name = folder_name
        self.file_prefix = file_prefix

    def filter(self, record: LogRecord) -> bool:  # noqa: A003
        try:
            res = (
                self.folder_name == folder_name_var.get()
                and self.file_prefix == file_prefix_var.get()
            )
        except LookupError:
            res = False
        return res


class FilterOnlyWithoutContext(Filter):
    def filter(self, record: LogRecord) -> bool:  # noqa: A003
        try:
            _ = folder_name_var.get()
            _ = file_prefix_var.get()
        except LookupError:
            res = True
        else:
            res = False
        return res


def set_logger_context(folder_name: str, file_prefix: str) -> None:
    folder_name_var.set(folder_name)
    file_prefix_var.set(file_prefix)


def set_logger_context_from_parent(parent_context: Context) -> None:
    for var, value in parent_context.items():
        if var in (file_prefix_var, folder_name_var):
            var.set(value)


def pass_log_context():
    parent_context = copy_context()
    return partial(set_logger_context_from_parent, parent_context)
