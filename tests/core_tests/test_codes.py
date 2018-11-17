import unittest

from rime.core import codes


class TestRunResult(unittest.TestCase):
    def test_init(self):
        run_result = codes.RunResult(codes.RunResult.OK, 1.0)
        self.assertEqual(run_result.status, codes.RunResult.OK)
        self.assertEqual(run_result.time, 1.0)


class TestCode(unittest.TestCase):
    def test_init(self):
        code = codes.Code('src', 'src_dir', 'out_dir')
        self.assertEqual(code.src_name, 'src')
        self.assertEqual(code.src_dir, 'src_dir')
        self.assertEqual(code.out_dir, 'out_dir')
        self.assertFalse(code.QUIET_COMPILE)
        self.assertIsNone(code.PREFIX)
        self.assertIsNone(code.EXTENSIONS)

    def test_compile(self):
        code = codes.Code('src', 'src_dir', 'out_dir')
        with self.assertRaises(NotImplementedError):
            code.Compile()

    def test_run(self):
        code = codes.Code('src', 'src_dir', 'out_dir')
        with self.assertRaises(NotImplementedError):
            code.Run(None, None, None, None, None, None)

    def test_clean(self):
        code = codes.Code('src', 'src_dir', 'out_dir')
        with self.assertRaises(NotImplementedError):
            code.Clean()


class TestCreateDictionary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class _TestCode(codes.Code):
            PREFIX = 'test'
            EXTENSIONS = ['test']

            def __init__(self, src_name, src_dir, out_dir):
                pass

        codes.registry.Add(_TestCode)
        cls._TestCode = _TestCode

    def test_create_dictionary(self):
        codeset = []
        exports = codes.CreateDictionary(
            '%s_src', codeset, 'src_dir', 'out_dir')
        self.assertIn('test_src', exports)
        self.assertEqual(codeset, [])
        exports['test_src']('main.test')
        self.assertEqual(len(codeset), 1)
        self.assertIsInstance(codeset[0], self._TestCode)

    def test_auto_code(self):
        codeset = []
        exports = codes.CreateDictionary(
            '%s_src', codeset, 'src_dir', 'out_dir')
        self.assertIn('auto_src', exports)
        exports['auto_src']('main.test')
        self.assertEqual(len(codeset), 1)
        self.assertIsInstance(codeset[0], self._TestCode)

    def test_auto_code_unknown_ext(self):
        codeset = []
        exports = codes.CreateDictionary(
            '%s_src', codeset, 'src_dir', 'out_dir')
        self.assertIn('auto_src', exports)
        with self.assertRaises(codes.UnknownCodeExtensionException):
            exports['auto_src']('main.err')
