# Three-Minute Presentation Script

## Slide 1 | Opening (about 15 seconds)

Good morning. We are Group 2, and our project examines nighttime traffic crashes in Taipei. In the next three minutes, I will explain why this study matters, how we plan to conduct it, and what we expect to learn.

## Slide 2 | Why (about 45 seconds)

Nighttime crashes do not occur in a single type of road environment. Urban intersections, late-night arterial roads, alleys, and peripheral roads differ in speed limits, road design, and weather conditions. A simple average comparison between lit and unlit roads may therefore hide important differences across crash contexts.

In Taipei's 2025 data, we initially identified about 6,795 nighttime injury crashes. Among crashes with known lighting conditions, 363 involved lights that were off or malfunctioning, and 97 occurred on unlit roads. We therefore ask whether these crashes form interpretable groups based on road, time, and environmental characteristics, and whether lighting problems and fatal-crash shares differ across those groups.

## Slide 3 | How (about 70 seconds)

First, we use Taipei's 2025 injury-crash records and define nighttime as the period from daily sunset to the following sunrise. Second, we construct features for crash time, speed limit, weather, road class, road form, and crash position. We one-hot encode categorical variables, standardize numerical variables, and apply cyclical transformations to time.

Third, we use principal component analysis to reduce dimensionality. We then use hierarchical clustering to examine the data structure and compare k-means solutions from two to six clusters. The final number of clusters will reflect elbow and silhouette evidence, stability, cluster size, and substantive interpretability rather than any single statistic.

The key design choice is that lighting conditions, deaths, and injuries do not enter the clustering model. We compare them only after clustering. This avoids defining groups directly from the outcomes and allows each cluster to represent a genuine crash context.

## Slide 4 | Expected Results (about 50 seconds)

We expect three main outputs. First, we will identify several stable and interpretable nighttime crash contexts and name them according to their observed profiles. Second, we will compare lighting conditions, fatal-crash shares, and confidence intervals across clusters. Third, we will combine each cluster's crash count and lighting-problem share to build a priority matrix for field inspection.

The value of this study is to help the city direct limited resources to the places most worth checking first, such as verifying whether streetlights are present, operating, or malfunctioning, and then collecting data on illumination, traffic volume, and road design. However, this is an exploratory and descriptive analysis. It provides inspection leads, not causal evidence that lighting improvements reduce crashes. Thank you.
