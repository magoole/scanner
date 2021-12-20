def ping(Host):
    """
    Returns True if Host responds to a ping request
    """
    import subprocess
    import platform

    # Ping parameters as function of OS
    ping_str = "-n 1" if platform.system().lower() == "windows" else "-c 1"
    args = "ping " + " " + ping_str + " " + Host
    need_sh = False if platform.system().lower() == "windows" else True

    # Ping
    return subprocess.call(args, shell=need_sh, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0
