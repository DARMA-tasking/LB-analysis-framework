#
#@HEADER
###############################################################################
#
#                                  lbsWeb.py
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Questions? Contact darma@sandia.gov
#
###############################################################################
#@HEADER
#
"""This module contains web utility methods."""
import os
from typing import Optional
from urllib.request import urlretrieve, urlparse
from urllib.error import HTTPError, URLError

from .lbsLogging import Logger


def download(
    url: str,
    target_dir: str,
    logger: Logger,
    expected_content_type: str = "text/plain",
    file_title: Optional[str] = None
):
    """Download a file to a local directory.

    :param url: The url
    :param target_dir: The directory where to place the downloaded file.
    :param logger: A logger instance for logs
    :param expected_content_type: Specify the expected content type of the file
    :param file_title: Used for logs. Defaults to the downloaded file name.

    :raises ConnectionError: on connection error
    :raises ConnectionError: on HTTP response error
    :raises ConnectionError: on invalid content type and if file has not already been downloaded
    """

    url_parsed = urlparse(url)
    filename = os.path.basename(url_parsed.path)
    if file_title is None:
        file_title = filename

    # Create src/lbaf/imported directory if not exist
    if not os.path.isdir(target_dir):
        os.makedirs(target_dir)

    # Create empty __init__.py file
    with open(os.path.join(target_dir, "__init__.py"), "wt", encoding="utf-8"):
        pass
    # Download the file
    try:
        logger.info(f"Retrieve {file_title} at {url}")
        tmp_filepath, http_message = urlretrieve(url, os.path.join(target_dir, '~' + filename))
        filepath = os.path.join(target_dir, filename)
        content_type = http_message.get_content_type()
        # Validate content type for script that has been retrieved
        if content_type == expected_content_type:
            os.rename(tmp_filepath, filepath)
            logger.info(f"Saved {file_title} to: {filepath}")
        else:
            # file is downloaded but not valid content type just remove
            if os.path.isfile(tmp_filepath):
                os.remove(tmp_filepath)

            if os.path.isfile(filepath):
                logger.error(
                    f"Unexpected Content-Type ({content_type}) for {file_title}"
                    " Using last valid {file_title}: {filepath}"
                )
            else:
                raise ConnectionError(
                    f"Unexpected Content-Type `{content_type}` for {file_title}" +
                    "downloaded from {script_url}\n"
                )
    except HTTPError as err:
        raise ConnectionError(f"Can not download file: {err.filename} \n"
                              f"Server responded with code: {err.fp.code} and message: {err.fp.msg}") from err
    except URLError as err:
        raise ConnectionError("Probably there is no internet connection") from err
