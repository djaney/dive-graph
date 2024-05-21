import click


from freediving.dive import Dive
from .data import get_dives_from_file, get_data, InvalidGarminFitFileError, InvalidZipFileError
import matplotlib.pyplot as plt


@click.command()
@click.argument("input_path", type=click.Path(exists=True, resolve_path=True))
@click.option("-i", "--index", type=int, help="Index of the dive to print. Interactive if not set")
@click.option("-p", "--pdf", "pdf", type=click.Path(exists=False), help="Create PDF")
def show_graph(input_path: click.Path, index=None, pdf=None):
    """
    Show a graph of the dive data.

    INPUT_PATH is the path to the zip or fit file
    """
    try:
        dives = get_dives_from_file(input_path)
    except InvalidGarminFitFileError:
        click.FileError("Invalid garmin fit file")
        return
    except InvalidZipFileError:
        click.FileError("Invali zip file")
        return
    except Exception as e:
        click.FileError(str(e))
        return

    # select
    if not pdf and index is None:
        for i, dive in enumerate(dives):
            click.echo(f"{i}. {int(dive.peak)}m")
        selection_idx = click.prompt("Which dive to show? (index)",
                                     type=click.Choice([str(i) for i, v in enumerate(dives)]), show_choices=False)
    else:
        selection_idx = index

    if pdf is not None:
        from matplotlib.backends.backend_pdf import PdfPages
        pp = PdfPages(pdf)
        figures = [_plot_dive(dive, i) for i, dive in enumerate(dives)]
        for fig in figures:
            fig.savefig(pp, format='pdf')
        pp.close()

    else:
        selection = dives[int(selection_idx)]
        _plot_dive(selection, 0)
        plt.show()






def _plot_dive(dive: Dive, figure_id: int):
    data = get_data(dive)
    (time_data, depth_data, rate_data) = data['data']
    alarms = data['alarms']
    mid_x = data['mid_x']
    peak_rate = data['peak_rate']
    max_depth = data['max_depth']

    fig = plt.figure(figure_id)

    ax1 = fig.add_subplot(1, 1, 1)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Depth')
    # plot dive
    line1 = ax1.plot(time_data, depth_data, color='tab:blue', label="Depth")
    # plot alarms
    for a in alarms:
        ax1.plot(*a, color='orange', marker='o')

    # second overlay
    ax2 = ax1.twinx()
    ax2.axhline(0, color='grey', )
    ax2.axvline(mid_x, color='grey', )

    line2 = ax2.plot(time_data, rate_data, color='tab:red', label="Rate")
    ax2.set_ylabel('Rate')
    ax2.set_ylim([-peak_rate, peak_rate])

    # fig.tight_layout()
    plt.title(f"{max_depth:.1f}m")

    # added these three lines
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    by_label = dict(zip(labels, lines))
    plt.legend(by_label.values(), by_label.keys(), loc=9)

    return fig


def _plot(dives):
    for i, dive in enumerate(dives):
        _plot_dive(dive, i)
