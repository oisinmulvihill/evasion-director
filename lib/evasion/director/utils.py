import logging


def log_init(level):
    """Used mainly in testing to create a default catch all logging set up

    This set up catches all channels regardless of whether they
    are in other projects or in our own project.

    """
    log = logging.getLogger()
    hdlr = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    log.setLevel(level)
    log.propagate = 0

