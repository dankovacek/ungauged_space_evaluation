# Ungauged Space Evaluation

This book documents an analysis of how well the existing streamflow monitoring
network in British Columbia represents the population of ungauged catchments.
Representation is measured using KL divergence (KLD) between unit-area runoff
distributions (flow duration curves) of gauged and ungauged sites.

A high minimum KLD between an ungauged basin and its most similar gauged
neighbours indicates that the catchment is poorly represented by the current
network. The analysis produces a ranked list of gauged stations by their
representation of the ungauged space, which can be used to support monitoring
network design decisions.

## Station Network Representation

The map below shows every gauged station in the network, coloured by how many
ungauged basins the station best represents (its "soft count" quintile).  The 
soft count is the number of ungauged basins for which the station is the most 
similar gauged neighbour, where fractional counts are assigned when multiple 
gauged stations are within a small tolerance (5%) of the minimum KLD.
Stations with no representation are shown as hollow circles. Hover over any
point to see its official station ID and soft count.

:::{bokeh-plot}
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bokeh.io import show
from plot_station_rankings import build_station_importance_map

show(build_station_importance_map())
:::
