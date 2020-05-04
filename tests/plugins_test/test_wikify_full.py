import unittest

import mock

from rime.plugins import wikify_full
from rime.util import struct


class TestWikifyFull(unittest.TestCase):
    def test_do_clean(self):
        ui = mock.MagicMock()
        ui.options = struct.Struct({'skip_clean': False})
        project = wikify_full.Project('project', 'base_dir', None)
        project.problems = []
        project.Clean = mock.MagicMock()

        task_graph = project._GenerateWikiFull(ui)
        task_graph.Continue()

        project.Clean.called_once_with(ui)

    def test_skip_clean(self):
        ui = mock.MagicMock()
        ui.options = struct.Struct({'skip_clean': True})
        project = wikify_full.Project('project', 'base_dir', None)
        project.problems = []
        project.Clean = mock.MagicMock()

        task_graph = project._GenerateWikiFull(ui)
        task_graph.Continue()

        project.Clean.assert_not_called()


if __name__ == '__main__':
    unittest.main()
