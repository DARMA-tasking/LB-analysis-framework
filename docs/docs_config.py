"""Configuration to generate the documentation."""
import lbaf

PROJECT_TITLE = "LBAF (Load Balancing Analysis Framework)"
INPUT = "../src/lbaf"
OUTPUT = "../../docs/output"

STYLESHEETS = [
    "https://fonts.googleapis.com/css?family=Source+Sans+Pro:400,400i,600,600i%7CSource+Code+Pro:400,400i,600",
    "../css/m-dark.compiled.css",
    "../css/m-dark.documentation.compiled.css"]
THEME_COLOR = "#22272e"

LINKS_NAVBAR1 = [
    ("LBAF", "pages",
     [("Getting started", "getting_started"),
      ("Configuration file", "configuration"),
      ("Input data", "input_data"),
      ("Usage", "usage"),
      ("Testing", "testing"),
      ("Utils", "utils"),
      ("Dependencies", "dependencies"),
      ]),
    ("Modules", "modules", []),
    ("Classes", "classes", [])]

PLUGINS = ["m.code", "m.components", "m.dox"]

INPUT_MODULES = [lbaf]

INPUT_PAGES = [
    "../../docs/pages/index.rst",
    "../../docs/pages/configuration.rst",
    "../../docs/pages/usage.rst",
    "../../docs/pages/getting_started.rst",
    "../../docs/pages/testing.rst",
    "../../docs/pages/utils.rst",
    "../../docs/pages/dependencies.rst",
    "../../docs/pages/input_data.rst"]
