from __future__ import absolute_import, division, unicode_literals

import itertools
import json
import os
import re
import tempfile
import zipfile
from io import open
from wsgiref.util import FileWrapper

from django.conf import settings
from django.utils.translation import ugettext as _

from celery import states
from celery.task import task
from celery.utils.log import get_task_logger

from soil import DownloadBase
from soil.util import expose_cached_download, expose_file_download

from corehq import toggles
from corehq.apps.app_manager.dbaccessors import get_app
from corehq.apps.hqmedia.cache import BulkMultimediaStatusCache
from corehq.apps.hqmedia.models import CommCareMultimedia
from corehq.util.files import file_extention_from_filename

logging = get_task_logger(__name__)

MULTIMEDIA_EXTENSIONS = ('.mp3', '.wav', '.jpg', '.png', '.gif', '.3gp', '.mp4', '.zip', )


@task(serializer='pickle')
def process_bulk_upload_zip(processing_id, domain, app_id, username=None, share_media=False,
                            license_name=None, author=None, attribution_notes=None):
    """
        Responsible for processing the uploaded zip from Bulk Upload.
    """

    status = BulkMultimediaStatusCache.get(processing_id)

    if not status:
        # no download data available, abort
        return

    app = get_app(domain, app_id)

    status.in_celery = True
    status.save()

    uploaded_zip = status.get_upload_zip()
    if not uploaded_zip:
        return

    zipped_files = uploaded_zip.namelist()
    status.total_files = len(zipped_files)
    checked_paths = []

    try:
        save_app = False
        for index, path in enumerate(zipped_files):
            status.update_progress(len(checked_paths))
            checked_paths.append(path)
            file_name = os.path.basename(path)
            try:
                data = uploaded_zip.read(path)
            except Exception as e:
                status.add_unmatched_path(path, _("Error reading file: %s" % e))
                continue

            media_class = CommCareMultimedia.get_class_by_data(data, filename=path)
            if not media_class:
                status.add_skipped_path(path, CommCareMultimedia.get_mime_type(data))
                continue

            app_paths = list(app.get_all_paths_of_type(media_class.__name__))
            app_paths_lower = [p.lower() for p in app_paths]
            form_path = media_class.get_form_path(path, lowercase=True)

            if not form_path in app_paths_lower:
                status.add_unmatched_path(path,
                                          _("Did not match any %s paths in application." % media_class.get_nice_name()))
                continue

            index_of_path = app_paths_lower.index(form_path)
            form_path = app_paths[index_of_path]  # this is the correct capitalization as specified in the form

            multimedia = media_class.get_by_data(data)
            if not multimedia:
                status.add_unmatched_path(path,
                                          _("Matching path found, but could not save the data to couch."))
                continue

            is_new = form_path not in app.multimedia_map
            is_updated = multimedia.attach_data(data,
                                                original_filename=file_name,
                                                username=username)

            if not is_updated and not getattr(multimedia, '_id'):
                status.add_unmatched_path(form_path,
                                          _("Matching path found, but didn't save new multimedia correctly."))
                continue

            if is_updated or is_new:
                multimedia.add_domain(domain, owner=True)
                if share_media:
                    multimedia.update_or_add_license(domain, type=license_name, author=author,
                                                     attribution_notes=attribution_notes)
                save_app = True
                app.create_mapping(multimedia, form_path, save=False)

            media_info = multimedia.get_media_info(form_path, is_updated=is_updated, original_path=path)
            status.add_matched_path(media_class, media_info)

        if save_app:
            app.save()
        status.update_progress(len(checked_paths))
    except Exception as e:
        status.mark_with_error(_("Error while processing zip: %s" % e))
    uploaded_zip.close()

    status.complete = True
    status.save()


def _get_file_path(app, include_multimedia_files, include_index_files, build_profile_id,
                   download_targeted_version):
    if settings.SHARED_DRIVE_CONF.transfer_enabled:
        fpath = os.path.join(settings.SHARED_DRIVE_CONF.transfer_dir, "{}{}{}{}{}".format(
            app._id,
            'mm' if include_multimedia_files else '',
            'ccz' if include_index_files else '',
            app.version,
            build_profile_id
        ))
        if download_targeted_version:
            fpath += '-targeted'
    else:
        dummy, fpath = tempfile.mkstemp()
    return fpath


def _ensure_all_media_files_in_ccz(fpath, errors):
    with open(fpath, 'rb') as tmp:
        with zipfile.ZipFile(tmp, "r") as z:
            media_suites = [f for f in z.namelist() if re.search(r'\bmedia_suite.xml\b', f)]
            if len(media_suites) != 1:
                message = _('Could not identify media_suite.xml in CCZ')
                errors.append(message)
            else:
                with z.open(media_suites[0]) as media_suite:
                    from corehq.apps.app_manager.xform import parse_xml
                    parsed = parse_xml(media_suite.read())
                    resources = {node.text for node in
                                 parsed.findall("media/resource/location[@authority='local']")}
                    names = z.namelist()
                    missing = [r for r in resources if re.sub(r'^\.\/', '', r) not in names]
                    errors += [_('Media file missing from CCZ: {}').format(r) for r in missing]


def _build_ccz_files(build, build_profile_id, include_multimedia_files, include_index_files,
                     download_id, compress_zip, filename, download_targeted_version):
    from corehq.apps.hqmedia.views import iter_app_files
    files, errors, file_count = iter_app_files(
        build, include_multimedia_files, include_index_files, build_profile_id,
        download_targeted_version=download_targeted_version,
    )

    if toggles.CAUTIOUS_MULTIMEDIA.enabled(build.domain):
        manifest = json.dumps({
            'include_multimedia_files': include_multimedia_files,
            'include_index_files': include_index_files,
            'download_id': download_id,
            'build_profile_id': build_profile_id,
            'compress_zip': compress_zip,
            'filename': filename,
            'download_targeted_version': download_targeted_version,
            'app': build.to_json(),
        }, indent=4)
        files = itertools.chain(files, [('manifest.json', manifest)])
    return files, errors, file_count


def _zip_ccs_files(fpath, files, current_progress, file_progress, file_count, compression, track_progress):
    with open(fpath, 'wb') as tmp:
        with zipfile.ZipFile(tmp, "w") as z:
            for path, data in files:
                # don't compress multimedia files
                extension = os.path.splitext(path)[1]
                file_compression = zipfile.ZIP_STORED if extension in MULTIMEDIA_EXTENSIONS else compression
                z.writestr(path, data, file_compression)
                current_progress += file_progress / file_count
                if track_progress:
                    DownloadBase.set_progress(build_application_zip, current_progress, 100)


def create_ccz_files(build, build_profile_id, include_multimedia_files=True, include_index_files=True,
                     download_id=None, compress_zip=False, filename="commcare.zip",
                     download_targeted_version=False, track_progress=False, expose_link=False):
    """
    :param track_progress: track progress of the files when being run asynchronously by celery
    :param expose_link: expose downloadable link for the file created
    :return: path to the ccz file
    """
    compression = zipfile.ZIP_DEFLATED if compress_zip else zipfile.ZIP_STORED
    current_progress = 10  # early on indicate something is happening
    file_progress = 50.0  # arbitrarily say building files takes half the total time

    if track_progress:
        DownloadBase.set_progress(build_application_zip, current_progress, 100)

    fpath = _get_file_path(build, include_multimedia_files, include_index_files, build_profile_id,
                           download_targeted_version)

    # Don't rebuild the file if it is already there
    if not (os.path.isfile(fpath) and settings.SHARED_DRIVE_CONF.transfer_enabled):
        files, errors, file_count = _build_ccz_files(build, build_profile_id, include_multimedia_files,
                                                     include_index_files, download_id, compress_zip,
                                                     filename, download_targeted_version)
        _zip_ccs_files(fpath, files, current_progress, file_progress, file_count, compression, track_progress)
        # Integrity check that all media files present in media_suite.xml were added to the zip
        if include_multimedia_files and include_index_files and toggles.CAUTIOUS_MULTIMEDIA.enabled(build.domain):
            _ensure_all_media_files_in_ccz(fpath, errors)
        if errors:
            os.remove(fpath)
            raise Exception('\t' + '\t'.join(errors))
    else:
        if track_progress:
            DownloadBase.set_progress(build_application_zip, current_progress + file_progress, 100)
    if expose_link:
        _expose_download_link(fpath, filename, compress_zip, download_id)
    if track_progress:
        DownloadBase.set_progress(build_application_zip, 100, 100)
    return fpath


def _expose_download_link(fpath, filename, compress_zip, download_id):
    common_kwargs = {
        'mimetype': 'application/zip' if compress_zip else 'application/x-zip-compressed',
        'content_disposition': 'attachment; filename="{fname}"'.format(fname=filename),
        'download_id': download_id,
        'expiry': (1 * 60 * 60),
    }
    if settings.SHARED_DRIVE_CONF.transfer_enabled:
        expose_file_download(fpath, use_transfer=True, **common_kwargs)
    else:
        expose_cached_download(FileWrapper(open(fpath, 'rb')),
                               file_extension=file_extention_from_filename(filename),
                               **common_kwargs)


@task(serializer='pickle')
def build_application_zip(include_multimedia_files, include_index_files, app,
                          download_id, build_profile_id=None, compress_zip=False, filename="commcare.zip",
                          download_targeted_version=False):
    DownloadBase.set_progress(build_application_zip, 0, 100)
    fpath = create_ccz_files(app, build_profile_id, include_multimedia_files, include_index_files,
                             download_id, compress_zip, filename, download_targeted_version,
                             track_progress=True, expose_link=True)
    _expose_download_link(fpath, filename, compress_zip, download_id)
    DownloadBase.set_progress(build_application_zip, 100, 100)
