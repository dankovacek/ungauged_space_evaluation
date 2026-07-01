# Monitoring Region Evaluation

## Ungauged Space Coverage Map

The map below shows the (predicted) representation gap across the unmonitored space in British Columbia. Each point represents an ungauged catchment, coloured by its minimum predicted KL divergence (KLD) to the nearest gauged station in the monitoring network. The green and orange triangles show active and discontinued streamflow monitoring stations, respectively.

## Methodology

### Prediction Process

For each ungauged basin, we predict the KL divergence between its flow-duration curve (FDC) and the FDC of every gauged station in the network. Predictions use XGBoost models trained on pairwise comparisons of gauged stations, using physical watershed attributes (e.g. slope, elevation, drainage area) and the Euclidean distance between basin centroids as features (see the [KL divergence prediction repository](https://github.com/dankovacek/divergence_prediction)). The model learns to predict log(KLD), and predictions are back-transformed with exp(). Trial 6 was selected (the trial whose median out-of-sample MAE is closest to the overall median across all trials).

### Point Selection and Classification

Only ungauged basins with minimum predicted KLD **greater than 1 bit** are plotted. This threshold excludes basins that are very well represented by at least one existing station (since KLD < 1 bit represents a small divergence in information terms). 

The plotted basins are classified into three groups by their minimum predicted KLD:
- **1–2 bits** (dark): basins with lower than median predicted KL divergence.
- **2–5 bits** (magenta): basins least well represented by the network.

### Station Network Overlay

The map shows all gauged stations within the bounding box of the plotted basins. Active stations (green) are currently in operation, while discontinued stations (orange) are no longer collecting data.

### Relationship to Station Importance

This overview map complements the station-importance map in the preceding section. Both use the same underlying predictions:
- The **station-importance map** (intro page) aggregates predictions from the basin side, ranking each gauged station by how many ungauged basins it best represents (the "soft count" allows fractional counts for near-ties between "best" stations).
- The **monitoring-region evaluation map** shows the same predictions from the basin side, highlighting where coverage gaps exist across the landscape and which stations may need attention or expansion to improve network representation.

These two views provide complementary perspectives on network adequacy: one identifies which stations are most valuable to the current ungauged space, and the other identifies which areas have the poorest coverage.  Here "coverage" means recoverability of the flow duration curve.


### Best-Donor CDF

The final comparison plot overlays two CDFs in the same KLD units used by the map colours: 1) minimum predicted KLD for each ungauged basin (best donor), and 2) pairwise station-to-station KLD values from the XGBoost training sample. Both curves are plotted with percentile sampling (200 points max), not all raw points. This makes the <1, 1-2, 2-5, and >5 bit map classes directly interpretable against the training distribution.

:::{bokeh-plot}
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bokeh.io import show
from plot_pred_dkl import build_ungauged_overview_map

show(build_ungauged_overview_map())
:::

The map above shows where higher or lower minimum KLD values occur in space. The two plots below provide the distribution context for those colours. The soft-count CDF panel shows how station representation concentration changes as the tie threshold increases, and the KLD CDF panel shows where the map classes sit relative to the station-pair training sample.

:::{bokeh-plot}
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bokeh.io import show
from plot_station_rankings import build_best_donor_cdf_plot

show(build_best_donor_cdf_plot())
:::
