"""Configuration to generate the documentation."""

# Applications
import lbaf.Applications.LBAF_app as LBAF

# Model

import lbaf.Model.lbsAffineCombinationWorkModel as AffineCombinationWorkModel
import lbaf.Model.lbsLoadOnlyWorkModel as LoadOnlyWorkModel
import lbaf.Model.lbsObject as Object
import lbaf.Model.lbsMessage as Message
import lbaf.Model.lbsObjectCommunicator as ObjectCommunicator
import lbaf.Model.lbsPhase as Phase
import lbaf.Model.lbsRank as Rank
import lbaf.Model.lbsWorkModelBase as WorkModelBase

# Execution
import lbaf.Execution.lbsAlgorithmBase as AlgorithmBase
import lbaf.Execution.lbsBruteForceAlgorithm as BruteForceAlgorithm
import lbaf.Execution.lbsCriterionBase as CriterionBase
import lbaf.Execution.lbsInformAndTransferAlgorithm as InformAndTransferAlgorithm
import lbaf.Execution.lbsPhaseStepperAlgorithm as PhaseStepperAlgorithm
import lbaf.Execution.lbsRuntime as Runtime
import lbaf.Execution.lbsStrictLocalizingCriterion as StrictLocalizingCriterion
import lbaf.Execution.lbsTemperedCriterion as TemperedCriterion

# Imported
import lbaf.imported.JSON_data_files_validator as JSONDataFilesValidator

# IO
import lbaf.IO.lbsConfigurationValidator as ConfigurationValidator
import lbaf.IO.lbsConfigurationUpgrader as configurationUpgrader
import lbaf.IO.lbsGridStreamer as GridStreamer
import lbaf.IO.lbsVisualizer as Visualizer
import lbaf.IO.lbsStatistics as lbsStatistics
import lbaf.IO.lbsVTDataReader as LoadReader
import lbaf.IO.lbsVTDataWriter as VTDataWriter

# Utilities
import lbaf.Utils.csv_2_json_data_converter as Csv2JsonConverter
import lbaf.Utils.data_stat_files_updater as DataStatFilesUpdater
import lbaf.Utils.exception_handler as exc_handler
import lbaf.Utils.logger as logger
import lbaf.Utils.vt_data_extractor as VTDataExtractor


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
     [("Before starting", "before_starting"),
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

INPUT_MODULES = [
    AffineCombinationWorkModel,
    LoadOnlyWorkModel,
    Object,
    Message,
    ObjectCommunicator,
    Phase,
    Rank,
    WorkModelBase,
    LBAF,
    AlgorithmBase,
    BruteForceAlgorithm,
    CriterionBase,
    InformAndTransferAlgorithm,
    PhaseStepperAlgorithm,
    Runtime,
    StrictLocalizingCriterion,
    TemperedCriterion,
    JSONDataFilesValidator,
    ConfigurationValidator,
    GridStreamer,
    Visualizer,
    lbsStatistics,
    LoadReader,
    VTDataWriter,
    Csv2JsonConverter,
    DataStatFilesUpdater,
    exc_handler,
    logger,
    VTDataExtractor,
    configurationUpgrader]

INPUT_PAGES = [
    "../../docs/pages/index.rst",
    "../../docs/pages/configuration.rst",
    "../../docs/pages/usage.rst",
    "../../docs/pages/before_starting.rst",
    "../../docs/pages/testing.rst",
    "../../docs/pages/utils.rst",
    "../../docs/pages/dependencies.rst",
    "../../docs/pages/input_data.rst"]
