import numpy as np 
import Figure1_replication as Fig1
import data_generation_rf_res_proj as dg
import matplotlib.pyplot as plt 

GRID_SIZE = 41 # 40 x 40 gray grid 
SIM_DURATION = 200 #200 ms of time points 
START_TIME = 20 #20 ms 


# Step 0 : Save Rfs as numpy arrays in data saved 3-D array, first dimension being every neuron type and second and third being the 2-D Gaussian rf itself 

lamina_rf = dg.save_neuron_rf(Fig1.LAMINA_NEURON, Fig1.LAMINA_NEURON_FWHM_CENTER, Fig1.LAMINA_NEURON_FWHM_SURROUND, Fig1.LAMINA_NEURON_SURROUND_FAC, Fig1.LAMINA_NEURON_POLARITY)
np.save("Aditi_fly_optic_lobe/data/lamina_rf.npy", lamina_rf)
T4_rf = dg.save_neuron_rf(Fig1.MEDULLA_NEURON_T4, Fig1.MEDULLA_NEURON_T4_FWHM_CENTER, Fig1.MEDULLA_NEURON_T4_FWHM_SURROUND, Fig1.MEDULLA_NEURON_T4_SURROUND_FAC, Fig1.MEDULLA_NEURON_T4_POLARITY)
np.save("Aditi_fly_optic_lobe/data/T4_rf.npy", T4_rf)
T5_rf = dg.save_neuron_rf(Fig1.MEDULLA_NEURON_T5, Fig1.MEDULLA_NEURON_T5_FWHM_CENTER, Fig1.MEDULLA_NEURON_T5_FWHM_SURROUND, Fig1.MEDULLA_NEURON_T5_SURROUND_FAC, Fig1.MEDULLA_NEURON_T5_POLARITY)
np.save("Aditi_fly_optic_lobe/data/T5_rf.npy", T5_rf)


# Step 1 : Define Stimulus 

center_flash = dg.flash_stim(0, 0, 20) #start time 
dg.plot_stimulus(center_flash, "flash at center", save_path= "Aditi_fly_optic_lobe/Results/flash_at_center_stim.png")

left_dot_right = dg.mving_dot_stim(0, 0, 20, "right")
dg.plot_stimulus(left_dot_right, "flash at center moving right", save_path= "Aditi_fly_optic_lobe/Results/moving_dot_stim.png")


# Step 2 : Calculate neuron activity using dot product of rf vs stimulus per time point; each dot product gives neuron activity at specific time i 

#lamina neuron load 

lamina = np.load("Aditi_fly_optic_lobe/data/lamina_rf.npy")

lamina_result_center_flash = dg.neuron_activity_family(center_flash, lamina)
dg.plot_result(lamina_result_center_flash, "Lamina Neuron : Center Flash Result RAW pre filters", Fig1.LAMINA_NEURON, save_path="Aditi_fly_optic_lobe/Results/Lamina_flash_at_center_results_RAW.png")

lamina_result_moving_dot = dg.neuron_activity_family(left_dot_right, lamina) 
dg.plot_result(lamina_result_moving_dot, "Lamina Neuron : Moving Dot Result RAW pre filters", Fig1.LAMINA_NEURON, save_path= "Aditi_fly_optic_lobe/Results/Lamina_moving_dot_results_RAW.png" )


# Step 3 : Apply filters to and plot final result 

filtered_lamina_center_flash = dg.neuron_filtered_result_family(lamina_result_center_flash, Fig1.LAMINA_NEURON_LP_TAU, Fig1.LAMINA_NEURON_HP_TAU) 
dg.plot_final_result(filtered_lamina_center_flash, "Lamina : Center Flash Result FILTERED", Fig1.LAMINA_NEURON, save_path= "Aditi_fly_optic_lobe/Results/Lamina_center_flash_results_FILTERED.png" )

filtered_lamina_moving_dot = dg.neuron_filtered_result_family(lamina_result_moving_dot, Fig1.LAMINA_NEURON_LP_TAU, Fig1.LAMINA_NEURON_HP_TAU) 
dg.plot_final_result(filtered_lamina_moving_dot, "Lamina : Moving Dot Result FILTERED", Fig1.LAMINA_NEURON, save_path= "Aditi_fly_optic_lobe/Results/Lamina_moving_dot_results_FILTERED.png" )
