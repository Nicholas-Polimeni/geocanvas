# geoplot_component.py
from matplotlib import pyplot as plt
from matplotlib.offsetbox import AnnotationBbox, TextArea
from pydantic import BaseModel
from typing import List, Optional
from utils import intelligently_place, create_text_box
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


class GeoCanvasComponent(BaseModel):
    def apply(self, geoplot):
        raise NotImplementedError("Subclasses must implement the apply method.")


class Choropleth(GeoCanvasComponent):
    column: str
    cmap: str = "viridis"

    def apply(self, geocanvas):
        # TODO: For now implemented with an overlay duplicate plot; in future, use plt.fill()
        gdf = geocanvas.plot_args.gdf
        ax = geocanvas.axes
        gdf.plot(column=self.column, cmap=self.cmap, ax=ax)


class Colorbar(GeoCanvasComponent):
    # place below title and subtitle

    def _guard_choropleth(self, geocanvas):
        # Guard method to ensure that a Choropleth component is present in the GeoCanvas
        choropleth = next(
            (c for c in geocanvas.components if c.__class__.__name__ == "Choropleth"),
            None,
        )

        if choropleth is None:
            raise ValueError(
                "A Choropleth component must be present in the GeoCanvas to add a Colorbar."
            )

        return choropleth

    def apply(self, geocanvas):
        choropleth = self._guard_choropleth(geocanvas)
        # TODO: place intelligently and scale
        ax = geocanvas.axes
        fig = geocanvas.figure

        # Create an inset axes for the colorbar
        cax = inset_axes(ax, width="5%", height="20%", loc="lower right", borderpad=1)

        sm = plt.cm.ScalarMappable(cmap=choropleth.cmap)
        sm._A = []

        fig.colorbar(sm, cax=cax, orientation="vertical")

        cax.yaxis.set_ticks_position("none")
        cax.yaxis.set_tick_params(length=0)
        # TODO make it so that the colorbar is in the current axis rather than a new one


class Title(GeoCanvasComponent):
    title: str
    subtitle: Optional[str] = None
    title_args: Optional[dict] = {
        "fontsize": 10,
        "fontweight": "bold",
        "fontname": "Arial",
    }
    subtitle_args: Optional[dict] = {
        "fontsize": 8,
        "fontweight": "normal",
        "fontname": "Arial",
    }

    def apply(self, geocanvas):
        # Add a title to the plot based on the specified arguments
        ax = geocanvas.axes
        x, y = intelligently_place(ax)

        # TODO: improve code and make dist between title and subtitle dynamic
        text_box = create_text_box(
            self.title,
            (x, y),
            text_args=self.title_args,
        )
        ax.add_artist(text_box)

        if self.subtitle:
            text_box = create_text_box(
                self.subtitle,
                (x, y - 0.05),
                text_args=self.subtitle_args,
            )
            ax.add_artist(text_box)


class Theme(GeoCanvasComponent):
    # TODO: add basemap
    background_color: Optional[str] = "white"
    # ... add more arguments as needed

    def apply(self, geocanvas):
        ax = geocanvas.axes
        ax.set_facecolor(self.background_color)

    # add bar to the side


# basemap
# subtitle
# source
# cases where there is no whitespace in figure, need to extend AX
class Label(GeoCanvasComponent):
    column: str

    def apply(self, geocanvas):
        gdf = geocanvas.plot_args.gdf
        ax = geocanvas.axes
        # TODO: intelligently locate area with most whitespace on axes for label placement
        gdf.apply(
            lambda x: ax.annotate(
                text=x[self.column], xy=x.geometry.centroid.coords[0], ha="center"
            ),
            axis=1,
        )


class Highlight(GeoCanvasComponent):
    geometries: List[int]

    def apply(self, geocanvas):
        # Highlight specific geometries based a subset of the GeoDataFrame
        gdf = geocanvas.plot_args.gdf
        ax = geocanvas.axes
        highlight_gdf = gdf[gdf.index.isin(self.geometries)]
        highlight_gdf.plot(ax=ax, color="red", edgecolor="black")


class Axes(GeoCanvasComponent):
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None

    def apply(self, geocanvas):
        ax = geocanvas.axes
        ax.set_axis_on()
        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(self.ylabel)
