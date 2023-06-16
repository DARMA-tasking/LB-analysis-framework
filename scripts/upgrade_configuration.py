"""A script to bulk upgrade LBAF configuration files"""
import sys

from lbaf import PROJECT_PATH
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
from lbaf.Utils.lbsLogging import get_logger
from lbaf.IO.lbsConfigurationUpgrader import ConfigurationUpgrader, UpgradeAction
from lbaf.Utils.lbsExceptionHandler import exc_handler

# Exception handler
sys.excepthook = exc_handler

# get and validate args
parser = PromptArgumentParser()
default_pattern = [
    "./config/**/*[.yml][.yaml]",
    "./tests/config/**/*[.yml][.yaml]"
]
parser.add_argument("-a", "--add", type=str, default=None,
                    help="Key name (tree dot notation) to add")
parser.add_argument("-r", "--remove", type=str, default=None,
                    help="The key name (tree dot notation) to remove. e.g. `work_model.paramters.foo`. " +
                    "Required for a remove operation.")
parser.add_argument("-v", "--value", type=str, default=None,
                    help="The initial value for a key to add.  e.g. `42`. Required for a add operation.")
parser.add_argument("-t", "--type", type=str, default="str",
                    help="Optional. The type of the initial value to set for a new key. Ex. `int`. Default `str`")
parser.add_argument("-p", "--pattern", nargs="+", type=str, default=default_pattern,
                    help="The list of patterns indicating which configuration files reside (path must be defined " +
                        "as relative to the project directory). Defaults `" + str.join(' ', default_pattern) + '`'
                    )
args = parser.parse_args()

ACTION = UpgradeAction.FORMAT_ONLY
KEY = None
if args.add:
    ACTION = UpgradeAction.ADD_KEY
    KEY = args.add
elif args.remove:
    ACTION = UpgradeAction.REMOVE_KEY
    KEY = args.remove

if args.add and args.remove:
    raise ValueError("Cannot set both add and remove args")
if args.add and not args.value:
    raise ValueError("Missing value (-v or --vvv xxx)")

# init logger
upg_logger = get_logger("upgrade", level="debug")
upg_logger.info("Script to bulk add or remove key to/from LBAF configuration files within the project")
upg_logger.info(
    "NOTICE: Remember that the keys must be defined first at the schema level defined in " \
    "the ConfigurationValidator class"
)

upgrader = ConfigurationUpgrader(logger=upg_logger)
upgrader.upgrade_all(
    pattern = args.pattern,
    relative_to=PROJECT_PATH,
    action=ACTION,
    key=KEY,
    value=args.value,
    value_type=args.type
)
