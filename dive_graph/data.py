from freediving.dive import Dive
from tempfile import TemporaryDirectory
import zipfile
import os
from freediving import fit_to_session


class InvalidGarminFitFileError(Exception):
    pass


class InvalidZipFileError(Exception):
    pass


def get_dives_from_file(input_path):
    with TemporaryDirectory() as tmp_dir:
        fit_file_path = None
        if input_path[-4:] == ".zip":
            with zipfile.ZipFile(str(input_path), 'r') as zip_ref:
                extracted = zip_ref.namelist()
                try:
                    fit_file_path = next(x for x in extracted if _is_activity_file(x))
                    zip_ref.extractall(tmp_dir, members=[fit_file_path])
                    fit_file_path = os.path.join(tmp_dir, fit_file_path)
                except StopIteration:
                    raise InvalidZipFileError
        elif input_path[-4:] == ".fit":
            if not _is_activity_file(input_path):
                raise InvalidGarminFitFileError
            fit_file_path = str(input_path)

        # get dives
        session = fit_to_session(fit_file_path)
    dives = []
    for idx in range(session.length):
        dive = session.get_dive(idx)
        dive.finish()
        dives.append(dive)
    return dives


def get_data(dive: Dive):
    time_data, depth_data, _ = dive.get_plot_data()
    start_ts = dive.timeline[0]['timestamp']

    def _point_to_x(p):
        return float((p['timestamp'] - start_ts).total_seconds())

    peak_rate = 0
    rate_data = []
    for p in dive.timeline:
        if 'rate' not in p:
            rate_data.append(0)
            continue
        peak_rate = max(peak_rate, abs(p['rate']))
        rate_data.append(p['rate'])

    data = (time_data, depth_data, rate_data)

    mid_x = _point_to_x(dive._peak)

    alarms = []
    for point in dive.timeline:
        if 'events' in point:
            alarms.append((_point_to_x(point), -point['depth']))

    return {
        "data": data,
        "mid_x": mid_x,
        "alarms": alarms,
        "peak_rate": peak_rate,
        "max_depth": dive._peak['depth'],
    }


def _is_activity_file(file_name):
    return file_name[-12:] == "ACTIVITY.fit"
