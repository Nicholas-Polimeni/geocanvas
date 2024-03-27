from typing import List, Optional
import geopandas as gpd
import matplotlib.pyplot as plt
from pydantic import BaseModel, validator
from components import GeoCanvasComponent


def geocanvas(self, **kwargs):
    return GeoCanvas(self, **kwargs)


gpd.GeoDataFrame.geocanvas = geocanvas


class GeoCanvasArgs(BaseModel):
    """
    Input arguments for the plot function.

    Attributes:
        df (gpd.GeoDataFrame): The GeoDataFrame to plot. Active geometry column must be set.
        figsize (tuple): The size of the figure in inches. Default is (10, 10).
    """

    gdf: gpd.GeoDataFrame
    figsize: Optional[tuple] = (10, 10)

    class Config:
        arbitrary_types_allowed = True

    @validator("gdf")
    def _validate_df(cls, value):
        if not isinstance(value, gpd.GeoDataFrame):
            raise ValueError("df must be a GeoDataFrame")
        return value

    @validator("figsize")
    def _validate_figsize(cls, value):
        if len(value) != 2 or any(
            not isinstance(x, (int, float)) or x <= 0 for x in value
        ):
            raise ValueError("figsize must be a tuple of two positive numbers")
        return value


class GeoCanvas:
    def __init__(self, gdf, **kwargs):
        self.plot_args = GeoCanvasArgs(gdf=gdf, **kwargs)
        self.fig, self.ax = self._setup_plot()
        self.components = []
        self.component_coords = []

    @property
    def axes(self):
        return self.ax

    @property
    def figure(self):
        return self.fig

    def _setup_plot(self):
        fig, ax = plt.subplots(figsize=self.plot_args.figsize)
        ax.set_axis_off()
        return fig, ax

    def _plot(self):
        self.plot_args.gdf.plot(ax=self.ax)
        for component in self.components:
            component.apply(self)
            component_coords = component.get_coords(self)

    def plot(self):
        """
        Plot the GeoCanvas with all additional components.

        Returns:
            bool: The result of the operation.

        Example:
            >>> import geopandas as gpd
            >>> world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
            >>> ax = plot_map(world, projection='Mercator', figsize=(12, 8), title='World Map')
        """
        self._plot()
        plt.show()

    def add_component(self, component: GeoCanvasComponent):
        """Adds a GeoPlotComponent to the GeoCanvas.

        Args:
            component (GeoPlotComponent): The component to add.
        """
        self.components.append(component)

    def __add__(self, other):
        self.add_component(other)
        return self

    def __repr__(self):
        # add CRS
        return f"GeoCanvas({self.gdf})"

    def __eq__(self, other):
        return self.gdf.equals(other.gdf)
