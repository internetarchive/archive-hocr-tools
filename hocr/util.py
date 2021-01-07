import gzip

def open_if_required(fd_or_path):
    if isinstance(fd_or_path, str):
        if fd_or_path.endswith('.gz'):
            xml_file = gzip.open(fd_or_path, 'rb')
        else:
            xml_file = open(fd_or_path, 'rb')
    else:
        xml_file = fd_or_path

    return xml_file
