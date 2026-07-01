# Monitoring Network Evaluation

This book documents an analysis of how well the streamflow monitoring
network represents the population of ungauged catchments.
Representation is expressed by predicted KL divergence (KLD) between unit-area runoff
distributions (flow duration curves) of gauged and ungauged sites.  The 
predicted KL divergence is based on XGBoost models trained on pairwise comparisons of gauged stations, using physical watershed attributes (e.g. slope, elevation, drainage area) and the Euclidean distance between basin centroids as predictive features.

A high minimum KLD between an ungauged basin and its most similar gauged
neighbours indicates that the catchment is poorly represented by the current
network. The analysis produces a ranked list of monitoring stations by their
representation of the ungauged space, which can be used to support monitoring
network design decisions.

## Station representation of the ungauged space

The map below shows every gauged station in the network, coloured by how many
ungauged basins the station best represents (its "soft count" quintile).  The 
soft count is the number of ungauged basins for which the station is the most 
similar gauged neighbour, where fractional counts are assigned when multiple 
gauged stations are within a small tolerance (5%) of the minimum KLD.
Stations with no representation are shown as hollow circles. Hover over any
point to see its station ID and soft count.

:::{bokeh-plot}
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bokeh.io import show
from plot_station_rankings import build_station_importance_map

show(build_station_importance_map())
:::
