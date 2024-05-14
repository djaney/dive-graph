import click
from tempfile import TemporaryDirectory
import zipfile
import os
from freediving import fit_to_session
from freediving.dive import Dive
import matplotlib.pyplot as plt
import numpy as np


@click.command()
@click.argument("input_path", type=click.Path(exists=True, resolve_path=True))
@click.option("-i", "--index", type=int, help="Index of the dive to print. Interactive if not set")
def show_graph(input_path: click.Path, index=None):
    """
    Show a graph of the dive data.

    INPUT_PATH is the path to the zip or fit file
    """
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
                    click.FileError("Invalid zip file")
        elif input_path[-4:] == ".fit":
            if not _is_activity_file(input_path):
                click.FileError("Invalid fit file")
            fit_file_path = str(input_path)

        # get dives
        session = fit_to_session(fit_file_path)
        dives = []
        for idx in range(len(session._dives)):
            dive = session.get_dive(idx)
            dive.finish()
            dives.append(dive)
        if index is None:
            for i, dive in enumerate(dives):
                click.echo(f"{i}. {int(dive._peak['depth'])}m")
            selection_idx = click.prompt("Which dive to show? (index)",
                                         type=click.Choice([str(i) for i, v in enumerate(dives)]), show_choices=False)
        else:
            selection_idx = index

        selection = dives[int(selection_idx)]
        dive.events_to_annotations()
        _show_graph(selection)


def _is_activity_file(file_name):
    return file_name[-12:] == "ACTIVITY.fit"


def _show_graph(dive: Dive):
    time_depth = dive.get_plot_data()
    start_ts = dive.timeline[0]['timestamp']

    def _point_to_x(p):
        return float((p['timestamp'] - start_ts).total_seconds())

    mid_x = _point_to_x(dive._peak)

    fig = plt.figure()

    ax1 = fig.add_subplot(1, 1, 1)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Depth')
    # plot dive
    line1 = ax1.plot(*time_depth, color='tab:blue', label="Depth")
    # plot alarms
    for point in dive.timeline:
        if 'events' in point:
            ax1.plot(_point_to_x(point), -point['depth'], color='orange', marker='o')

    # second overlay
    ax2 = ax1.twinx()
    ax2.axhline(0, color='grey', )
    ax2.axvline(mid_x, color='grey', )

    rates = (time_depth[0], [])
    peak_rate = 0
    for p in dive.timeline:
        peak_rate = max(peak_rate, abs(p['rate']))
        rates[1].append(p['rate'])
    line2 = ax2.plot(rates[0], rates[1], color='tab:red', label="Rate")
    ax2.set_ylabel('Rate')
    ax2.set_ylim([-peak_rate, peak_rate])

    # fig.tight_layout()
    plt.title(f"{dive._peak['depth']:.1f}m")

    # added these three lines
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    by_label = dict(zip(labels, lines))
    plt.legend(by_label.values(), by_label.keys(), loc=9)

    plt.show()
