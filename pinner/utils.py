import posix_ipc

def create_or_get_queue(name):
    """ 
    Try and create a POSIX IPC message queue or open one if it already exists 
    """
    queue = None
    try:
        queue = posix_ipc.MessageQueue(name, posix_ipc.O_CREX)
    except posix_ipc.ExistentialError as err:
        if 'already exists' in str(err):
            queue = posix_ipc.MessageQueue(name)
    return queue