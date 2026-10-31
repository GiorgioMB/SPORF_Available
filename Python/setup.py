"""Build script for the rerf package (Python bindings to packedForest).

Build requirements are declared in pyproject.toml. To upload to PyPI see
PUBLISH.md.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import find_packages, setup
from setuptools.errors import CompileError

here = os.path.abspath(os.path.dirname(__file__))

PACKAGE_NAME = "rerf"
DESCRIPTION = "Randomer Forest (RerF) Python Package"
URL = "https://github.com/neurodata/RerF"
AUTHOR = "NeuroData"
AUTHOR_EMAIL = "software@neurodata.io"


def read_version():
    """Read __version__ from rerf/__init__.py without importing the package."""
    with open(os.path.join(here, "rerf", "__init__.py"), encoding="utf-8") as f:
        match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', f.read(), re.M)
    if match is None:
        raise RuntimeError("Unable to find __version__ in rerf/__init__.py")
    return match.group(1)


with open(os.path.join(here, "requirements.txt"), encoding="utf-8") as f:
    required = [line.strip() for line in f if line.strip() and not line.startswith("#")]

with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()


OPENMP_TEST_PROGRAM = """
#include <omp.h>
int main() {
    int n = 0;
    #pragma omp parallel reduction(+ : n)
    n += 1;
    return n > 0 ? 0 : 1;
}
"""


def homebrew_libomp_prefixes():
    """Return existing Homebrew libomp prefixes (for Apple clang on macOS)."""
    candidates = []
    if shutil.which("brew"):
        result = subprocess.run(
            ["brew", "--prefix", "libomp"], capture_output=True, text=True
        )
        if result.returncode == 0:
            candidates.append(result.stdout.strip())
    candidates += ["/opt/homebrew/opt/libomp", "/usr/local/opt/libomp"]

    prefixes = []
    for prefix in candidates:
        if prefix and prefix not in prefixes:
            if os.path.isfile(os.path.join(prefix, "include", "omp.h")):
                prefixes.append(prefix)
    return prefixes


def compiles(compiler, extra_args):
    """Return True if the OpenMP test program compiles with extra_args."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "openmp_test.cpp")
        with open(source, "w") as f:
            f.write(OPENMP_TEST_PROGRAM)
        try:
            compiler.compile([source], output_dir=tmpdir, extra_postargs=extra_args)
        except CompileError:
            return False
    return True


def openmp_flags(compiler):
    """Return (compile_args, link_args) that enable OpenMP, or None.

    Set RERF_DISABLE_OPENMP=1 to skip the check and build single-threaded.
    """
    if os.environ.get("RERF_DISABLE_OPENMP"):
        return None

    if compiler.compiler_type == "msvc":
        candidates = [(["/openmp"], [])]
    else:
        # GCC, and LLVM clang where libomp is installed.
        candidates = [(["-fopenmp"], ["-fopenmp"])]
        if sys.platform == "darwin":
            # Apple clang needs the Homebrew libomp runtime passed explicitly.
            for prefix in homebrew_libomp_prefixes():
                candidates.append(
                    (
                        ["-Xpreprocessor", "-fopenmp", "-I" + prefix + "/include"],
                        ["-L" + prefix + "/lib", "-lomp"],
                    )
                )

    for compile_args, link_args in candidates:
        if compiles(compiler, compile_args):
            return compile_args, link_args
    return None


class BuildExt(build_ext):
    """build_ext that adds optimisation flags and OpenMP when available."""

    def build_extensions(self):
        msvc = self.compiler.compiler_type == "msvc"
        compile_args = [] if msvc else ["-O3", "-DNDEBUG", "-ffast-math"]
        link_args = []

        flags = openmp_flags(self.compiler)
        if flags is not None:
            compile_args += flags[0]
            link_args += flags[1]
        else:
            print(
                "WARNING: OpenMP was not found, so rerf is being built without "
                "multithreading (n_jobs will have no effect). On macOS, "
                "'brew install libomp' and reinstall to enable it.",
                file=sys.stderr,
            )
            if not msvc:
                compile_args.append("-Wno-unknown-pragmas")

        for ext in self.extensions:
            ext.extra_compile_args = list(ext.extra_compile_args) + compile_args
            ext.extra_link_args = list(ext.extra_link_args) + link_args
        super().build_extensions()


ext_modules = [
    Pybind11Extension(
        "pyfp",
        ["src/packedForest.cpp"],
        include_dirs=["src/src/"],
        cxx_std=14,
    )
]


setup(
    name=PACKAGE_NAME,
    version=read_version(),
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    ext_modules=ext_modules,
    install_requires=required,
    python_requires=">=3.8",
    cmdclass={"build_ext": BuildExt},
    zip_safe=False,
    url=URL,
    license="Apache License 2.0",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
)
