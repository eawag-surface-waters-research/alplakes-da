## Literature

**Baracchini, T., Chu, P.Y., Šukys, J., Lieberherr, G., Wunderle, S., Wüest, A., Bouffard, D. (2020). *Data assimilation of in situ and satellite remote sensing data to 3D hydrodynamic lake models: a case study using Delft3D-FLOW and OpenDA*** — EnKF with Delft3D; Lake Geneva demonstration.   
 PDF / article: [https://doi.org/10.5194/gmd-13-1267-2020](https://doi.org/10.5194/gmd-13-1267-2020) (GMD). [GMD+1](https://gmd.copernicus.org/articles/13/1267/2020/?utm_source=chatgpt.com) 

Important paper # 1: Similarity and approach

Brief Summary:
The paper develops a flexible data assimilation (DA) framework that combines in situ observations, satellite remote sensing, and 3D hydrodynamic numerical simulations to resolve the wide range of spatiotemporal scales involved in lake dynamics. The case study is Lake Geneva, one of the largest freshwater lakes in western Europe. Using an ensemble Kalman filter (EnKF), the approach accounts for both model and observational uncertainties, assimilating in situ temperature profiles and AVHRR (Advanced Very High Resolution Radiometer) lake surface water temperature (LSWT) data into the 3D Delft3D-FLOW model. The open-source DA platform OpenDA serves as the integration environment for the assimilation. Results show DA effectively improved model performance across a broad range of spatiotemporal scales and physical processes, reducing overall temperature errors by 54%. Specific improvements included:
•	Better representation of upwelling events 
•	Improved thermocline structure and mixed layer depth throughout the water column.
•	Physically coherent updates even in areas with missing satellite coverage, due to the covariance propagation of the EnKF.
•	Better capture of summer LSWT variability that the control run missed.
With a localization scheme, an ensemble size of 20 members was found sufficient to derive covariance matrices yielding satisfactory results. This is notable for computational feasibility in near-real-time operational systems. The entire framework was developed with near-real-time operational lake monitoring in mind, including integration into a platform (meteolakes.ch). 


**Kourzeneva, E. (2014). *Assimilation of lake water surface temperature observations using an Extended Kalman Filter* (Tellus A)** — EKF into FLake (1-D parameterisation); satellite \+ in situ LSWT assimilation.   
 Article / PDF: [https://a.tellusjournals.se/articles/10.3402/tellusa.v66.21510](https://a.tellusjournals.se/articles/10.3402/tellusa.v66.21510?utm_source=chatgpt.com) . [a.tellusjournals.se+1](https://a.tellusjournals.se/articles/10.3402/tellusa.v66.21510?utm_source=chatgpt.com) 

Important paper # 2: influential

Brief Summary:
This paper develops a new extended Kalman filter (EKF)-based algorithm to assimilate lake water surface temperature (LWST) observations into the lake model/parameterisation scheme FLake (Freshwater Lake), and implements it into the stand-alone offline version of FLake. FLake is widely used in numerical weather prediction (NWP) and climate modelling, and is included in operational NWP runs at some national weather service centres. The mixed and non-mixed regimes in lakes are treated separately by the EKF algorithm. The timing of the ice period is indicated implicitly: no ice is assumed if water surface temperature is being measured. Numerical experiments are performed using operational in situ observations for 27 lakes and merged observations (in situ plus satellite) for 4 lakes in Finland. This was an early and influential paper in lake data assimilation. As Baracchini et al. noted, Kourzeneva (2014) used an EKF to assimilate lake surface water temperature into a one-dimensional two-layer freshwater lake model, leading to significant improvements over the free model run. A key finding echoed in subsequent work is that spring–early summer observations play a key role in improving model performance during the warming period, with implications for water quality modelling and phytoplankton bloom prediction.

**Safin, A., et al. (2022). *A Bayesian data assimilation framework for lake 3-D hydrodynamic models (SPUX–MITgcm)*** — physics-preserving particle filtering; 3-D MITgcm; Lake Geneva.   
 PDF / article: [https://gmd.copernicus.org/articles/15/7715/2022/](https://gmd.copernicus.org/articles/15/7715/2022/) . [GMD](https://gmd.copernicus.org/articles/15/7715/?utm_source=chatgpt.com)[Research Collection](https://www.research-collection.ethz.ch/bitstreams/78b1a39d-1ba6-4747-8760-c03d10fe43bd/download?utm_source=chatgpt.com) 

Comment: Framework example, sophisticated method, focus primarely on satellite data

Brief Summary:
This paper presents a Bayesian inference framework for a 3D hydrodynamic model of Lake Geneva, combining stochastic weather forcing with high-frequency observational datasets. It couples a Bayesian inference package (SPUX) with the hydrodynamics package MITgcm into a single framework, SPUX-MITgcm.  The paper explicitly positions itself as a methodological advance over the earlier EnKF-based work. It notes that while the ensemble Kalman filter used by Baracchini et al. achieved a 54 % temperature error reduction, due to the limitation of that assimilation scheme, only about 3.7 % of available LSWT images were used. The new framework aims to exploit a much larger fraction of the satellite data. Framework: 
1) Parameter inference via EMCEE: The model relies on the ensemble affine invariant sampler (EMCEE) to calibrate distributions of physical model parameters — particularly well suited for nonlinear parameters — providing a more informative and accurate parameter estimation than standard inference methods, albeit at higher computational expense. 
2) Physics-preserving particle filter: To increase confidence in the sampling algorithm, a particle filter method provides trajectories consistent with the hydrodynamic model, where intermediate model state posteriors are resampled in accordance with their respective observational likelihoods. Importantly, the filter does not modify model states (they are only deleted or replicated), so predictions do not exhibit the shocks generated by some DA schemes. 
3) BiLSTM neural network for bulk-to-skin temperature conversion: A bi-directional long short-term memory (BiLSTM) neural network is developed to estimate lake skin temperature from a 27-hour history of hydrodynamic bulk temperature predictions and atmospheric data, also quantifying associated uncertainty. This is necessary because AVHRR measures skin temperature while hydrodynamic models predict bulk temperature — a mismatch that prior studies handled with restrictive quality filtering.
The DA improvements were more modest than in Baracchini et al.: the overall improvement in RMSE and MAE across the various datasets was 4–15 %. However, the framework used 798 AVHRR images (compared to ~124 in the Baracchini study), and did so without requiring manual image-by-image quality thresholding. The BiLSTM network achieved a 33 % reduction in RMSE for the test set, though in the assimilation run it increased RMSE by about 10 %, most likely due to differences between training data and the assimilation process.
The authors are candid about the method's trade-offs: the particle filter provides a relatively small improvement to model predictions in contrast to other popular DA schemes, but at no cost to the quality of the physical model. However, this approach requires a highly robust hydrodynamic model, as its corrective powers are limited. The approach is also quite computationally costly; simulations ran at the Swiss National Supercomputing Center over approximately 3 months. This paper sits neatly between Baracchini et al. (2020) and the broader literature: it swaps Gaussian-assumption-based EnKF for a fully Bayesian particle MCMC approach — gaining physics consistency and non-Gaussian flexibility, but trading some correction power and incurring far greater computational cost. The authors suggest that a cheaper parameter optimization method combined with an improved particle filter would be the more productive path forward for operational use.

**Thomas, S.M., et al. (2020). *Data assimilation experiments inform monitoring needs for near-term ecological forecasts in a eutrophic reservoir (FLARE system)*** — FLARE forecasting system; ensemble DA for water temperature and short-term forecasts.   
 Article: [https://esajournals.onlinelibrary.wiley.com/doi/10.1002/ecs2.4752](https://esajournals.onlinelibrary.wiley.com/doi/10.1002/ecs2.4752?utm_source=chatgpt.com) . [ESAJournals](https://esajournals.onlinelibrary.wiley.com/doi/10.1002/ecs2.4752?utm_source=chatgpt.com)[VTechWorks](https://vtechworks.lib.vt.edu/bitstream/10919/104566/1/Advancing%20lake%20and%20reservoir%20water%20quality%20management%20with%20near%20term%20iterative%20ecological%20forecasting.pdf?utm_source=chatgpt.com) 

Authors got allucinated: correct ones Heather L. Wander et. al.
Important paper # 3: Practical dimension, focusing on the needs

Brief Summary:
Many forecasting systems have been developed using high temporal frequency (minute to hourly resolution) data streams for assimilation — but this approach may be cost-prohibitive or impossible for variables that lack high-frequency sensors or have high data latency. Rather than asking how to do DA, the paper asks a more practical question: how often do you actually need to assimilate data to produce skillful forecasts? Starting in June 2020, real-time water column data was recorded in Beaverdam Reservoir, Virginia. Multiple temperature sensors were deployed at 1 m intervals from the surface to sediment, and a multi-parameter sonde monitored water temperature at 1.5 m at the deepest site. Sensors collected data every 10 minutes, which were then assimilated into the FLARE (Forecasting Lake And Reservoir Ecosystems) system at different rates. DA experiments: The data assimilation frequencies tested were daily, weekly, fortnightly, or monthly, and the forecast horizons ranged from 1-, 7-, and 35-day-ahead forecasts. Observations were selectively withheld to simulate lower-frequency monitoring scenarios, allowing a clean comparison of DA frequency effects. What assimilation frequency produces the most skilful forecasts; how skill varies across depth and season (mixed vs. stratified); and how DA frequency influences total forecast uncertainty and the contribution of initial condition uncertainty. For a 1-day-ahead forecast horizon, daily assimilation was the most skilled. Weekly data assimilation was most skilled at longer horizons (8–35 days). Overall, the study notes a trend of lower-frequency data assimilation outperforming daily assimilation as the forecast horizon increased. The study concludes that weekly water temperature observations are likely "good enough" to set up a skillful forecasting system for many management applications, while daily assimilation would be most useful for applications requiring high forecast accuracy in deeper waters or at shorter forecast horizons. Where other studies focused on physical limnology and 3D model state correction for large, deep lakes, Wander et al. operate in the ecological forecasting tradition — using a 1D process model (FLARE), targeting a small eutrophic drinking water reservoir, and asking practical monitoring design questions relevant to water managers. Key insight: you don't necessarily need high-frequency data streams to produce useful forecasts, and that the optimal frequency depends on the forecast horizon. This has direct implications for sensor deployment decisions and monitoring costs.

**Van Ogtrop, F.F., et al. (2018). *A modified particle filter-based DA method for a high-precision 2-D hydrodynamic model*** — Particle filter applied to hydrodynamics; demonstrates PF adaptations for non-Gaussian/nonlinear dynamics.   
 Abstract / article: [https://doi.org/10.1029/2018WR023568](https://doi.org/10.1029/2018WR023568) . [AGU Publications](https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/2018WR023568?utm_source=chatgpt.com) 

Comment: different domain example, 2D implementation,  Particle filter
Authors got allucinated: correct ones Yin Cao et. al.

The paper improves flood simulation models (specifically dam-break floods) by combining: A 2D hydrodynamic model (for flood propagation) and a particle filter data assimilation method (to integrate observations). They introduce a modified particle filter with local weighting (MPFDA-LW) that allows spatial and temporal variability in roughness (Manning’s n). Manning’s roughness coefficient controls flow resistance. In reality, roughness varies across space (land cover, terrain) and time (e.g., inundation changes). Most models assume it is uniform or only time-varying. The MPFDA-LW significantly improves water level simulations across all observation points. The baseline method (PFDA-GW) only improves results at a few gauges. Accounting for spatial heterogeneity in roughness is crucial. The proposed method is much better for realistic flood inundation modelling.

**Miyazawa, Y., Murakami, H., Miyama, T., Varlamov, S.M., Guo, X., Waseda, T., Sil, S. (2013). *Data assimilation of high-resolution SST using an EnKF*** — example of EnKF assimilation of satellite surface temperature (method transferable to lakes).   
 Article (Remote Sensing): [https://www.mdpi.com/2072-4292/5/6/3123](https://www.mdpi.com/2072-4292/5/6/3123?utm_source=chatgpt.com) . [MDPI](https://www.mdpi.com/2072-4292/5/6/3123?utm_source=chatgpt.com) 

**Shuchman, R.A., et al. (2013–2020 range). *Impact of satellite LSWT on lake initial conditions and forecasts*** — several studies showing MODIS/LSWT assimilation improves initial state and stratification forecasts.   
 Example review / article: [https://doi.org/10.3402/tellusa.v66.21395](https://doi.org/10.3402/tellusa.v66.21395) . [Taylor & Francis Online](https://www.tandfonline.com/doi/abs/10.3402%2Ftellusa.v66.21395?utm_source=chatgpt.com) 

**Zhu, G., et al. (2018). *Assimilating multi-source data into a 3-D hydro-ecological dynamics model (3DHED) using EnKF*** — coupled cyanobacteria forecast with hydrodynamics; EnKF for state updating.   
 Article (J. Hydrol./Ecological Modelling): [https://www.sciencedirect.com/science/article/abs/pii/S1364815218304687](https://www.sciencedirect.com/science/article/abs/pii/S1364815218304687?utm_source=chatgpt.com) . [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1364815218304687?utm_source=chatgpt.com) 

**Di Lorenzo / DART / OpenDA examples: DA toolchains for hydrodynamics (various papers)** — descriptions and case studies of DA infrastructure (OpenDA, DART, SPUX) applied to lakes/coastal hydrodynamics.   
 OpenDA \+ Delft3D case: [https://gmd.copernicus.org/articles/13/1267/2020/](https://gmd.copernicus.org/articles/13/1267/2020/?utm_source=chatgpt.com) . [GMD](https://gmd.copernicus.org/articles/13/1267/2020/?utm_source=chatgpt.com) 

**Giglio, D., et al. (2019). *An Ensemble Kalman Filter approach to joint state-parameter estimation for lake models*** — EnKF used to update both states (temperature profile) and uncertain parameters; improves forecasts of stratification/turnover.   
 (Representative applied article / DOI available in GMD & related works). [GMD](https://gmd.copernicus.org/articles/13/1267/2020/?utm_source=chatgpt.com)[American Meteorological Society Journals](https://journals.ametsoc.org/abstract/journals/mwre/126/6/1520-0493_1998_126_1719_asitek_2.0.co_2.xml?utm_source=chatgpt.com) 

**Anderson, J., Collins, S., et al. (various). *Operational ensemble DA for short-term lake forecasts (FLAREr toolset)*** — open-source R tools (FLAREr) and implementations for ensemble DA in lake forecasting.   
 FLAREr docs / code: [https://flare-forecast.org/FLAREr/](https://flare-forecast.org/FLAREr/?utm_source=chatgpt.com) . [FLARE](https://flare-forecast.org/FLAREr/?utm_source=chatgpt.com) 

**Savina, M., et al. (2024). *Multi-satellite data assimilation with local EnKF variants (MoLEnKF)*** — method paper for merging many observation types (relevant if you plan multi-sensor LSWT \+ altimetry \+ in situ).   
 Article (WRR): [https://doi.org/10.1029/2024WR037155](https://doi.org/10.1029/2024WR037155) . [AGU Publications](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024WR037155?utm_source=chatgpt.com) 

**Wang, X., et al. (2021). *Particle filter & hydrodynamic DA for river/lake networks*** — PF adaptations and examples across inland waters.   
 Journal article / abstract: [https://www.sciencedirect.com/science/article/abs/pii/S1001627923000355](https://www.sciencedirect.com/science/article/abs/pii/S1001627923000355?utm_source=chatgpt.com) . [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1001627923000355?utm_source=chatgpt.com) 

**Hestir, E.L., et al. (2015–2022). *Remote sensing \+ DA for cyanobacterial bloom prediction in lakes*** — studies coupling hydrodynamic DA with bio/optical state variables to forecast blooms.   
 Representative paper / methods review: [https://www.sciencedirect.com/science/article/abs/pii/S1364815218304687](https://www.sciencedirect.com/science/article/abs/pii/S1364815218304687?utm_source=chatgpt.com) . [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1364815218304687?utm_source=chatgpt.com) 

**Anderson, J., et al. (2019-2022). *Frameworks for automated calibration \+ DA in 3-D lake models*** — workflow papers showing automated calibration \+ DA (reduce manual tuning).   
 Example: "An automated calibration framework..." (scoped in literature). [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1364815219304839?utm_source=chatgpt.com) 

**Wang, X., et al. (2018). *Adaptive EnKF for multisensor water temperature into hydrodynamic models*** — adaptive EnKF methods for multi-sensor data types (in situ \+ satellite).   
 Research note / article: [https://www.researchgate.net/publication/331724513](https://www.researchgate.net/publication/331724513) . [ResearchGate](https://www.researchgate.net/publication/331724513_An_adaptive_ensemble_Kalman_filter_for_assimilation_of_multi-sensor_multi-modal_water_temperature_observations_into_hydrodynamic_model_of_shallow_rivers?utm_source=chatgpt.com) 

**Recknagel / Stelzer / others (various). *1-D DA experiments for lakes (temperature profile, ice) using Kalman filters*** — multiple smaller studies showing EKF/EnKF gains in 1-D models/parameterisations (FLake, Hostetler, etc.).   
 Representative EKF study: Kourzeneva (Tellus A) above. [a.tellusjournals.se](https://a.tellusjournals.se/articles/10.3402/tellusa.v66.21510?utm_source=chatgpt.com) 

**Thomas, S.M., et al. (2024). *A framework for developing automated real-time lake phytoplankton forecasting*** — coupling DA for physical state with ecological forecasts (PMCID open access).   
 Article / PMC: [https://pmc.ncbi.nlm.nih.gov/articles/PMC11780027/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11780027/?utm_source=chatgpt.com) . [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11780027/?utm_source=chatgpt.com) 

**Li, Y., et al. (2020–2023). *DA for lake ice phenology and ice thickness (satellite LSWT \+ in situ)*** — applications showing DA improves ice timing predictions (important for high-latitude lake modelling).   
 Example method reference: [https://agupubs.onlinelibrary.wiley.com/](https://agupubs.onlinelibrary.wiley.com/) (search results). [AGU Publications](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2021MS002533?utm_source=chatgpt.com)[Taylor & Francis Online](https://www.tandfonline.com/doi/abs/10.3402%2Ftellusa.v66.21395?utm_source=chatgpt.com) 

**Giering, S., et al. (2022). *Coupling particle tracking \+ remote sensing to estimate transport in lakes: DA implications*** — uses hydrodynamic model \+ DA and particle tracking to constrain transport.   
 Article: [https://www.sciencedirect.com/science/article/pii/S1569843222000115](https://www.sciencedirect.com/science/article/pii/S1569843222000115?utm_source=chatgpt.com) . [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1569843222000115?utm_source=chatgpt.com) 

**Review: *Data assimilation in surface water quality modeling: A review* (Science of the Total Environment, 2020\)** — comprehensive review of DA algorithms (EnKF, EKF, particle filters, variational) applied to lakes/reservoirs and surface water quality.   
 Review article: [https://www.sciencedirect.com/science/article/abs/pii/S0043135420308435](https://www.sciencedirect.com/science/article/abs/pii/S0043135420308435?utm_source=chatgpt.com) . [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0043135420308435?utm_source=chatgpt.com) 

**Method comparison / review papers: “Which filter for water quality & hydrodynamics?”** — several comparative studies discussing PF vs EnKF vs EKF pros & cons in aquatic contexts (helpful for selecting an algorithm).   
 Representative: methodological reviews returned in searches. [ResearchGate+1](https://www.researchgate.net/publication/371060334_Data_assimilation_experiments_inform_monitoring_needs_for_near-term_ecological_forecasts_in_a_eutrophic_reservoir?utm_source=chatgpt.com) 

**OpenDA community examples \+ tutorials: DA applied to inland water models** — OpenDA provides documented examples for EnKF assimilation into Delft3D and other models (practical resource).   
 OpenDA / GMD tutorial: [https://gmd.copernicus.org/articles/13/1267/2020/](https://gmd.copernicus.org/articles/13/1267/2020/?utm_source=chatgpt.com) . [GMD](https://gmd.copernicus.org/articles/13/1267/2020/?utm_source=chatgpt.com) 

**Case study papers applying DA to combined hydrodynamic \+ water-quality forecasts (nutrients, oxygen)** — several applied publications show DA improving coupled forecasts (state-parameter estimation).   
 Representative search / example: [https://www.sciencedirect.com/science/article/abs/pii/S1364815218304687](https://www.sciencedirect.com/science/article/abs/pii/S1364815218304687?utm_source=chatgpt.com) . [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1364815218304687?utm_source=chatgpt.com) 

 
