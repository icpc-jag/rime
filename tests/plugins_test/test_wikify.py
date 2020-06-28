import unittest

import mock

from rime.plugins import wikify
from rime.util import struct


class TestWikify(unittest.TestCase):
    def setUp(self):
        project = wikify.Project('project', 'base_dir', None)
        project.wikify_config_defined = True
        project.Clean = mock.MagicMock()
        project.Test = mock.MagicMock()
        project._Summarize = mock.MagicMock()
        project._UploadWiki = mock.MagicMock()
        self.project = project

    def test_do_clean(self):
        ui = mock.MagicMock()
        ui.options = struct.Struct({'skip_clean': False})

        task = self.project.Wikify(ui)
        while task.Continue():
            pass

        self.project.Clean.assert_called_once_with(ui)
        self.project.Test.assert_called_once_with(ui)

    def test_skip_clean(self):
        ui = mock.MagicMock()
        ui.options = struct.Struct({'skip_clean': True})

        task = self.project.Wikify(ui)
        while task.Continue():
            pass

        self.project.Clean.assert_not_called()
        self.project.Test.assert_called_once_with(ui)


if __name__ == '__main__':
    unittest.main()
