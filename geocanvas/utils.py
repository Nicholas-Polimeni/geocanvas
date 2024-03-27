from matplotlib.offsetbox import AnnotationBbox
import numpy as np
from shapely.geometry import Polygon, box
import scipy.ndimage as ndimage
from matplotlib import pyplot as plt
from matplotlib.collections import PatchCollection
from shapely.ops import unary_union
from shapely.validation import make_valid
from matplotlib.offsetbox import AnnotationBbox, TextArea


def _collect_valid_geom(ax: plt.Axes):
    geometries = []
    for artist in ax.get_children():
        if isinstance(artist, PatchCollection):
            for patch in artist.get_paths():
                vertices = patch.vertices
                geometry = Polygon(vertices)
                geometries.append(geometry)
        if isinstance(artist, AnnotationBbox):
            # TODO: simplify
            bbox = artist.get_window_extent(ax.figure.canvas.get_renderer())
            bbox_coords = ax.transData.inverted().transform(bbox)

            x0, y0 = bbox_coords[0]
            x1, y1 = bbox_coords[1]
            annotation_geometry = Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
            geometries.append(annotation_geometry)

    return [make_valid(geom) for geom in geometries]


def _get_grid_boxes(x_range: np.ndarray, y_range: np.ndarray, n: int):
    grid_boxes = []
    for i in range(n):
        for j in range(n):
            grid_box = box(x_range[i], y_range[j], x_range[i + 1], y_range[j + 1])
            grid_boxes.append(grid_box)
    return grid_boxes


def _calculate_empty_space_grid(empty_area: Polygon, grid_boxes: list):
    empty_area_within_box = []

    for grid_box in grid_boxes:
        empty_area_box = empty_area.intersection(grid_box)
        if empty_area_box.is_empty:
            empty_area_within_box.append(0.0)
        else:
            empty_area_within_box.append(empty_area_box.area)

    return empty_area_within_box


def find_largest_empty_area(ax: plt.Axes, n: int = 8):
    """_summary_

    Args:
        ax (plt.Axes): _description_
        n (int, optional): _description_. Defaults to 8.
    """
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    axes_area = box(xmin, ymin, xmax, ymax)

    geometries = _collect_valid_geom(ax)
    occupied_space = unary_union(geometries)
    empty_area = axes_area.difference(occupied_space)

    x_range = np.linspace(xmin, xmax, n + 1)
    y_range = np.linspace(ymin, ymax, n + 1)
    grid_boxes = _get_grid_boxes(x_range, y_range, n)
    empty_space_grid = _calculate_empty_space_grid(empty_area, grid_boxes)
    convolution_filter = np.array([[1, 1, 1], [1, 7, 1], [1, 1, 1]])
    empty_space_grid = np.array(empty_space_grid).reshape((n, n))

    convovled_empty_space_grid = ndimage.convolve(
        empty_space_grid, convolution_filter, mode="reflect"
    )
    max_empty_space = grid_boxes[np.argmax(convovled_empty_space_grid)]

    return max_empty_space.centroid.x, max_empty_space.centroid.y


def intelligently_place(ax: plt.Axes, n: int = 8):
    """Alias for find_largest_empty_area

    Args:
        ax (plt.Axes): _description_
        n (int, optional): _description_. Defaults to 8.
    """
    return find_largest_empty_area(ax, n)


def create_text_box(text: str, coords: tuple, text_args: dict):
    """_summary_

    Args:
        text (str): _description_
        x (_type_): _description_
        y (tuple): _description_
        text_args (dict): _description_

    Returns:
        _type_: _description_
    """
    offsetbox = TextArea(
        text,
        textprops=text_args,
    )
    return AnnotationBbox(
        offsetbox,
        coords,
        box_alignment=(0.0, 0.5),
        frameon=False,
    )
