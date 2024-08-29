import unittest

import mock
import shutil
import tempfile

from rime.plugins import htmlify_full
from rime.util import struct


class TestHtmlifyProject(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        project = htmlify_full.Project('project', self.tmpdir, None)
        project.Clean = mock.MagicMock()
        project.Test = mock.MagicMock()
        project._Summarize = mock.MagicMock(return_value='result')
        self.project = project

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_do_clean(self):
        ui = mock.MagicMock()
        ui.options = struct.Struct({'skip_clean': False})

        task = self.project.HtmlifyFull(ui)
        while task.Continue():
            pass

        self.project.Test.assert_called_once_with(ui)
        self.project.Clean.assert_called_once_with(ui)

    def test_skip_clean(self):
        ui = mock.MagicMock()
        ui.options = struct.Struct({'skip_clean': True})

        task = self.project.HtmlifyFull(ui)
        while task.Continue():
            pass

        self.project.Test.assert_called_once_with(ui)
        self.project.Clean.assert_not_called()


if __name__ == '__main__':
    unittest.main()
