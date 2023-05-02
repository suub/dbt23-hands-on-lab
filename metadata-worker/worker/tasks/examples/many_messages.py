from worker.nw.log import get_logger
from worker.nw.utils import Result, Many

logger = get_logger(__name__)
logger.setLevel("DEBUG")


def run(args):
    number_of_messages_to_create = args["params"].get("messages")
    logger.debug(f"Creating {number_of_messages_to_create} messages")
    return Result(data=Many([i for i in range(number_of_messages_to_create)]))
