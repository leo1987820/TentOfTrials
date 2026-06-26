import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_PATH = ROOT / "build.py"


def load_build_module():
    spec = importlib.util.spec_from_file_location("tent_build", BUILD_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ModuleSelectionTests(unittest.TestCase):
    def setUp(self):
        self.build = load_build_module()

    def test_parse_module_selection_trims_comma_separated_names(self):
        self.assertEqual(
            self.build.parse_module_selection(" backend, frontend ,market "),
            ["backend", "frontend", "market"],
        )

    def test_validate_module_selection_rejects_unknown_names_with_available_modules(self):
        with self.assertRaises(ValueError) as error:
            self.build.validate_module_selection(["backend", "missing"])

        message = str(error.exception)
        self.assertIn("missing", message)
        self.assertIn("backend", message)
        self.assertIn("frontend", message)

    def test_validate_module_selection_returns_all_modules_for_all(self):
        selected = self.build.validate_module_selection(["all"])

        self.assertEqual([module.name for module in selected], [module.name for module in self.build.MODULES])

    def test_list_modules_flag_outputs_module_details(self):
        result = subprocess.run(
            [sys.executable, str(BUILD_PATH), "--list-modules"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Available modules:", result.stdout)
        self.assertIn("backend (Rust)", result.stdout)
        self.assertIn("frontend (TypeScript)", result.stdout)
        self.assertIn("build: cargo build", result.stdout)

    def test_invalid_module_cli_exits_with_valid_module_names(self):
        result = subprocess.run(
            [sys.executable, str(BUILD_PATH), "--module", "backend, missing"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        output = result.stdout + result.stderr
        self.assertIn("Unknown modules:", output)
        self.assertIn("missing", output)
        self.assertIn("Available:", output)
        self.assertIn("backend", output)
        self.assertIn("frontend", output)


if __name__ == "__main__":
    unittest.main()
