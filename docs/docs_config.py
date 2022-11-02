import os
import sys
try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-2])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    raise SystemExit(1)
# Applications
import src.lbaf.Applications.LBAF_app as LBAF
# Model
import src.lbaf.Model.lbsAffineCombinationWorkModel as AffineCombinationWorkModel
import src.lbaf.Model.lbsLoadOnlyWorkModel as LoadOnlyWorkModel
import src.lbaf.Model.lbsObject as Object
import src.lbaf.Model.lbsMessage as Message
import src.lbaf.Model.lbsObjectCommunicator as ObjectCommunicator
import src.lbaf.Model.lbsPhase as Phase
import src.lbaf.Model.lbsRank as Rank
import src.lbaf.Model.lbsWorkModelBase as WorkModelBase
# Execution
import src.lbaf.Execution.lbsAlgorithmBase as AlgorithmBase
import src.lbaf.Execution.lbsBruteForceAlgorithm as BruteForceAlgorithm
import src.lbaf.Execution.lbsCriterionBase as CriterionBase
import src.lbaf.Execution.lbsInformAndTransferAlgorithm as InformAndTransferAlgorithm
import src.lbaf.Execution.lbsPhaseStepperAlgorithm as PhaseStepperAlgorithm
import src.lbaf.Execution.lbsRuntime as Runtime
import src.lbaf.Execution.lbsStrictLocalizingCriterion as StrictLocalizingCriterion
import src.lbaf.Execution.lbsTemperedCriterion as TemperedCriterion
# imported
import src.lbaf.imported.JSON_data_files_validator as JSONDataFilesValidator
# IO
import src.lbaf.IO.configurationValidator as ConfigurationValidator
import src.lbaf.IO.lbsGridStreamer as GridStreamer
import src.lbaf.IO.lbsMeshBasedVisualizer as MeshBasedVisualizer
import src.lbaf.IO.lbsStatistics as lbsStatistics
import src.lbaf.IO.lbsVTDataReader as LoadReader
import src.lbaf.IO.lbsVTDataWriter as VTDataWriter
# Utils
import src.lbaf.Utils.csv_2_json_data_converter as Csv2JsonConverter
import src.lbaf.Utils.data_stat_files_updater as DataStatFilesUpdater
import src.lbaf.Utils.exception_handler as exc_handler
import src.lbaf.Utils.logger as logger
import src.lbaf.Utils.vt_data_extractor as VTDataExtractor


PROJECT_TITLE = 'LBAF (Load Balancing Analysis Framework)'
INPUT = '../src/lbaf'
OUTPUT = '../../docs/output'

STYLESHEETS = [
    'https://fonts.googleapis.com/css?family=Source+Sans+Pro:400,400i,600,600i%7CSource+Code+Pro:400,400i,600',
    '../css/m-dark.compiled.css',
    '../css/m-dark.documentation.compiled.css']
THEME_COLOR = '#22272e'

LINKS_NAVBAR1 = [
    ('Modules', 'modules', []),
    ('Classes', 'classes', [])]

PLUGINS = ['m.code', 'm.components', 'm.dox']

INPUT_MODULES = [AffineCombinationWorkModel, LoadOnlyWorkModel, Object, Message, ObjectCommunicator, Phase, Rank,
                 WorkModelBase, LBAF, AlgorithmBase, BruteForceAlgorithm, CriterionBase, InformAndTransferAlgorithm,
                 PhaseStepperAlgorithm, Runtime, StrictLocalizingCriterion, TemperedCriterion, JSONDataFilesValidator,
                 ConfigurationValidator, GridStreamer, MeshBasedVisualizer, lbsStatistics, LoadReader, VTDataWriter,
                 Csv2JsonConverter, DataStatFilesUpdater, exc_handler, logger, VTDataExtractor]

INPUT_PAGES = ['../../docs/pages/index.rst']
