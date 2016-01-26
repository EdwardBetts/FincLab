import queue
import logging
import logging.handlers


que = queue.Queue()  # no limit on size
queue_handler = logging.handlers.QueueHandler(que)
handler = logging.StreamHandler()
listener = logging.handlers.QueueListener(que, handler)

logger = logging.getLogger("FUCK ME")
logger.addHandler(queue_handler)

formatter = logging.Formatter("%(threadName)s: %(message)s")
handler.setFormatter(formatter)

listener.start()

logger.warning("FUCK OFF!")
logger.warning("OH OFF!")
logger.warning("FUCK AROUND!")

listener.stop()
