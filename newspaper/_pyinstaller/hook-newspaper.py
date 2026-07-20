# PyInstaller hook for newspaper4k
#
# Collects all data files (stopwords, user-agents, source lists, …) that are
# shipped inside the ``newspaper/resources/`` directory so they are available
# at runtime inside a frozen application.

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("newspaper")
