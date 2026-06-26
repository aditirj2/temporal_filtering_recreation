import numpy as np
import Figure1_replication as Fig1
import matplotlib.pyplot as plt 

#constants

GRID_SIZE = 41 # 40 x 40 gray grid 
SIM_DURATION = 200 #200 ms of time points 

# save 2-D receptive fields as numpy arrays for easy access later, grouped by neuron type 

def save_neuron_rf(neuron_name, FWHM_center, FWHM_surround,surround_fac, polarity) :

    
    
    size = len(neuron_name)

    output = np.zeros((size, 41, 41)) #3-D array, first dimension being every neuron and second and third being the 2-D Gaussian RF

    for i in range(size):

        #calculate rf 
        rf = Fig1.calc_rf(FWHM_center[i], 
                    FWHM_surround[i], 
                    surround_fac[i], 
                    polarity[i])
        
        output[i] = rf 
    
    return output  #this is 41 x 41 array 

#create stimulus 

#create 3D array 
def empty_stim(square_grid_size, sim_duration) :
   
   size = square_grid_size
   stim = np.zeros((size, size, sim_duration))  #changing grid to 41 x 41 to be able to access all elements, middle is 20, 20

   return stim 

def stim_value(coor_x, coor_y) :

    x = coor_x + 20  #(0,0 -> (20,20) which is middle   
    y = coor_y + 20 

    return x, y

#stimulus one : pixel on stays on  

def flash_stim(coor_x, coor_y, start_time, end_time = SIM_DURATION) :  # INSTRUCTIONS pick between -20 to 20 for x and y 

    stim = empty_stim(GRID_SIZE, SIM_DURATION)
    x = coor_x + 20  #(0,0 -> (20,20) which is middle   
    y = coor_y + 20 

    for i in range(start_time, end_time) : 
        
        stim[x][y][i] = 1.0

    #add some note hre for make sure you enter correct coordinates later 

    return stim

#stimulus two : moving dot 

def mving_dot_stim(coor_x, coor_y, start_time, direction, end_time = SIM_DURATION, step_size = 1) : 

    stim = empty_stim(GRID_SIZE, SIM_DURATION)
    starting_x,starting_y = stim_value(coor_x, coor_y) 
    current_pos_y = starting_y
    current_pos_x = starting_x  

    if direction == "up":
        
        for i in range(end_time - start_time) :  #think of linear equation; it is a dot!  
                
            #change value in grid 
            stim[current_pos_y][current_pos_x][i + start_time] = 1.0
            #update position 
            next_pos_y = current_pos_y - step_size #opposite as this is matrix 
            prev_pos_y = current_pos_y
            current_pos_y = next_pos_y

            if current_pos_y < 0 or current_pos_y >= GRID_SIZE:
                break

    if direction == "down" :

         for i in range(end_time - start_time) :  #think of linear equation; it is a dot!  
                
            stim[current_pos_y][current_pos_x][i + start_time] = 1.0
            next_pos_y = current_pos_y + step_size #opposite as column structure is different 
            prev_pos_y = current_pos_y
            current_pos_y = next_pos_y

            if current_pos_y < 0 or current_pos_y >= GRID_SIZE:
                break


    if direction == "left" :

        for i in range(end_time - start_time) :  #think of linear equation; it is a dot!  
                
            stim[current_pos_y][current_pos_x][i + start_time] = 1.0
            next_pos_x = current_pos_x - step_size #opposite as column structure is different 
            prev_pos_x = current_pos_x
            current_pos_x = next_pos_x

            if current_pos_x < 0 or current_pos_x >= GRID_SIZE:
                break

    if direction == "right" :
        
         for i in range(end_time - start_time) :  #think of linear equation; it is a dot!  
                
            stim[current_pos_y][current_pos_x][i + start_time] = 1.0
            next_pos_x = current_pos_x + step_size #opposite as column structure is different 
            prev_pos_x = current_pos_x
            current_pos_x = next_pos_x

            if current_pos_x < 0 or current_pos_x >= GRID_SIZE:
                break

    return stim 


def plot_stimulus(stimulus, title, save_path = None) : 

    fig, axes = plt.subplots(1, 3, figsize=(20, 5))
    times = [20, 25, 35]

    for i, t in enumerate(times):
        axes[i].imshow(stimulus[:, :, t], cmap='gray', vmin=-1, vmax=1)
        axes[i].set_title(f't={t}')

    plt.suptitle(title)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    plt.show()

## dot product

def neuron_activity_family(stimulus, neuron_family_rf, stim_duration = SIM_DURATION) :

    n_neurons = len(neuron_family_rf) #len on a 3-D array returns the size of the first dimension (5,40,40)
    activity = np.zeros((n_neurons, stim_duration))

    for i in range(n_neurons) :

        activity[i] = dot_product(stimulus, neuron_family_rf[i], stim_duration)

    return activity 


def dot_product(stimulus, rf, stim_duration) :
    
    if stimulus[:, :, 0].shape != rf.shape :
        return 0  
    
    activity = np.zeros(stim_duration)

    for i in range(stim_duration) : 
        
        activity[i] = np.sum(stimulus[:, :, i] * rf) #elementwise multiplication and then add up all the values to return dot product 

    return activity 

def plot_result(result, title, neuron_titles, save_path = None) : 

    fig, axes = plt.subplots(1, len(result), figsize=(20, 5))

    for i in range(len(result)):
        axes[i].plot(result[i])
        axes[i].set_title(neuron_titles[i])
    
    plt.suptitle(title)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    plt.show()

def temporal_filter(result, lp_tau, hp_tau) : 
     
    low = Fig1.low_pass(lp_tau, stim = result)

    if hp_tau == 0:
        final_filtered = low
    else: 
        final_filtered = Fig1.high_pass(hp_tau, low)
    
    final_filtered = Fig1.normalize(final_filtered)   # from borst 

    return final_filtered 

def neuron_filtered_result_family(raw_result_family, neuorn_family_lp_tau, neuron_family_hp_tau, stim_duration = SIM_DURATION) :

    n_neurons = len(raw_result_family) 
    activity = np.zeros((n_neurons, stim_duration))

    for i in range(n_neurons) :

        activity[i] = temporal_filter(raw_result_family[i], neuorn_family_lp_tau[i], neuron_family_hp_tau[i]) 
    
    return activity 


def plot_final_result(filtered_result, title, neuron_titles, save_path = None) : 

    fig, axes = plt.subplots(1, len(filtered_result), figsize=(20, 5))

    for i in range(len(filtered_result)):
        axes[i].plot(filtered_result[i])
        axes[i].set_title(neuron_titles[i])
    
    plt.suptitle(title)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    plt.show()