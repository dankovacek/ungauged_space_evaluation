# Monitoring Region Evaluation

## Ungauged Space Coverage Map

The map below shows the predicted representation gap across all ungauged basins in British Columbia. Each point represents an ungauged catchment, coloured by its minimum predicted KL divergence (KLD) to the nearest gauged station in the monitoring network. The green and orange triangles show active and discontinued gauged stations respectively.

## Methodology

### Prediction Process

For each ungauged basin, we predict the KL divergence between its flow-duration curve (FDC) and the FDC of every gauged station in the network. Predictions use XGBoost models trained on pairwise comparisons of gauged stations, using physical watershed attributes (e.g. slope, elevation, drainage area) and the Euclidean distance between basin centroids as features. The model learns to predict log(KLD), and predictions are back-transformed with exp(). Trial 6 was selected (the trial whose median out-of-sample MAE is closest to the overall median across all trials), and all five fold models for that trial are averaged.

### Point Selection and Classification

Only ungauged basins with minimum predicted KLD **greater than 1 bit** are plotted. This threshold excludes basins that are very well represented by at least one existing station (since KLD < 1 bit represents a small divergence in information terms). 

The plotted basins are classified into three groups by their minimum predicted KLD:
- **1–2 bits** (dark): basins with reasonable representation, though some divergence remains.
- **2–5 bits** (medium): basins with moderate to significant gaps in coverage.
- **5+ bits** (bright pink): basins with poor representation, indicating substantial gaps between their FDC and the network.

### Station Network Overlay

The map shows all gauged stations within the geographic bounding box of the plotted basins. Active stations (green) are currently in operation, while discontinued stations (orange) are no longer collecting data.

### Relationship to Station Importance

This overview map complements the station-importance map in the preceding section. Both use the same underlying predictions:
- The **station-importance map** (intro page) aggregates predictions from the basin side, ranking each gauged station by how many ungauged basins it best represents (the "soft count" allows fractional counts for near-ties between "best" stations).
- The **monitoring-region evaluation map** shows the same predictions from the basin side, highlighting where coverage gaps exist across the landscape and which stations may need attention or expansion to improve network representation.

Together, these two views provide complementary perspectives on network adequacy: one identifies which stations are most valuable to the current ungauged space, and the other identifies which areas have the poorest coverage.

:::{bokeh-plot}
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bokeh.io import show
from plot_pred_dkl import build_ungauged_overview_map

show(build_ungauged_overview_map())
:::
