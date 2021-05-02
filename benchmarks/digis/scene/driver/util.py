import time
import uuid
import urllib.request
import hashlib
from tqdm import tqdm
from functools import wraps


def timed(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        ts = time.time()
        result = f(*args, **kwds)
        te = time.time()
        if "log_time" in kwds:
            name = kwds.get("log_name", f.__name__.upper())
            kwds["log_time"][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.3f s' % (f.__name__, (te - ts) * 1))
        return result

    return wrapper


def uuid_str(num_char=5):
    return str(uuid.uuid4())[:num_char]


def digest(s, n=5):
    return hashlib.sha224(s).hexdigest()[:n]


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_url(url, output_path):
    with DownloadProgressBar(unit='B', unit_scale=True,
                             miniters=1, desc=url.split('/')[-1]) as t:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)
