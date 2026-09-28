import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
import blindschleiche_py3 as bs
import Medulla_Library as ml 
from scipy.signal import chirp
from scipy.optimize import minimize
import time 


#--CONSTANTS---#

E_exc = 10 #in mV
E_inh = -70 #mV
threshold = -50 #mv 

E_leak_all = -50 #mV
E_leak_lamina = -20 #mV higher potential what does this say? means closer to depolarization threshold... easier to excite / constantly releasing NT?  

E_leak = np.zeros(325) + E_leak_all #all neurons leak is -50 
for i in range(5) : 
    E_leak[65*i+8:65*i+12] = E_leak_lamina 

capac = 40 #pF
temp_res = 10 #ms
g_leak = 1 #nS

cdt = capac / temp_res
max_time = 200 #ms
sim_start = 50 #ms 
max_iter = 500


#------PHASE 1: Data & Setup -----------------------------------------------------

exc_synweight = 0.001
inh_synweight = 0.001
intial_current = +40 

num_col = 5
num_cells_per_col = 65
total_cells = num_col * num_cells_per_col 

number_of_param = num_cells_per_col * 2 #130

#--- load data ##

dir_name = "Aditi_fly_optic_lobe"
output_dir = dir_name + "/circuits"
multi_colM = np.load(output_dir + "/multi_colM_rec.npy") #loading multicolM matrix (325,325)
c_type =  np.load(output_dir + "/c_type_rec.npy") #load ctype array (65,)
mc_index = np.load(output_dir + "/mc_cell_index_rec.npy")


def init_network(): #initialize signal, data, and split connectivity matrices 

    M_inh = inh_synweight * multi_colM * (multi_colM < 0) * (-1)
    M_exc = exc_synweight * multi_colM * (multi_colM > 0)

    #signal matrix
    signal = np.zeros((total_cells, max_time))
    #input current to photoreceptors 
    signal[130:138, sim_start:max_time] = intial_current

    #for optimization
    data = ml.read_RecF_data() * 20.0  #20 mV threshold 

    #cost_array 
    cost_array = np.zeros(max_iter*number_of_param)

    return M_inh, M_exc, signal, data, cost_array

M_inh, M_exc, signal, data, cost_array = init_network() # tuple in order 

def pre_synaptic_vol_input(x, trsh) : #this is pre syanptic cell volt contribution... if cells voltage is lower than firing threshold, contributes no voltage to post syanptic cell 
 
    input = x - trsh     
    input = input * (input > 0) #returns boolean : 1 if true 0 if not element-wise
    
    return input 

def compute_Vnew_step(V_old, input_gain, output_gain, signal, M_inh, M_exc) : #input signal arr (325,) @specific time as well as split z param arr (65,) x2 
  
    #math : psvi returns 325 arr. output gain is 325. 
    #elementwise mulitplicatio of psvi and og give 325 arr. matrix is 325 x 325 dot product returns 325. 
    #elementwise mult w input gain give gexec for EACH post synaptic neuron as it is based on Vm  
    output = output_gain*pre_synaptic_vol_input(V_old, trsh=threshold)

    g_exc = input_gain*np.dot(M_exc, output) 
    g_inh = input_gain*np.dot(M_inh, output)

    num = g_leak*E_leak + g_exc*E_exc + g_inh*E_inh + cdt*V_old + signal 
    denom = cdt + g_leak + g_exc + g_inh
    V_new = num / denom 

    return V_new 

def calc_network(input_gain, output_gain, signal, M_inh, M_exc) :

    network = np.zeros((total_cells, max_time))
    V_old = E_leak
    network[:,0] = V_old

    for i in range(1,max_time) :

        V_new = compute_Vnew_step(V_old, input_gain, output_gain, signal[:, i-1], M_inh, M_exc)
        network[:,i] = V_new
        V_old = V_new

    return network 

def given_one_col_z_return_all_col(param_one_col) : 

    params_mul_col = np.zeros(len(param_one_col)*num_col)  #size 325 arr

    for col in range(num_col) :

        params_mul_col[num_cells_per_col*col+0:num_cells_per_col*col+65] = param_one_col

    return params_mul_col


def split_z(z) : #split z into first 65 (input params) and second 65 (output) ; then repeat for each col for plug into network equation

    input_params = z[0:65]
    output_params = z[65:130]

    input_gain = given_one_col_z_return_all_col(input_params)
    output_gain = given_one_col_z_return_all_col(output_params)

    return input_gain, output_gain 

def calc_model(z) : 

    #split z into input and output gains remember z 130 params
    input_gain, output_gain = split_z(z)

    network = calc_network(input_gain, output_gain, signal, M_inh, M_exc)

    optimize_cells = network[mc_index, :] #select cells to feed into model (65,300) arr

    #create model arr (13,9,200)
    model = np.zeros((13,9,200))

    for col in range(5): 
        model[:, col+2,:] = optimize_cells[0+13*col:13+13*col, :] 

    #different specifications, adding for reproducibility; can test if make a difference... 
    # removes DC value before stimulation
    
    interim = np.transpose(model,axes=(2,0,1)) - model[:,:,49]
    model  = np.transpose(interim,axes=(1,2,0))
    
    model[:,:,0:50] = 0 #zero beginning 
    
    # accounts for Ca-buffering
        
    model  = bs.lowpass(model,Ca_tau/deltat)
    
    # shift backwards one time pointm but leaves last point
    
    model[:,:,0:199] = model[:,:,1:200]
    
    return model 

def cost(model, data) :

    num = (model - data)**2
    denom = data**2
    total_cost = num/denom

    return total_cost

def calc_cost(z) : 

    global counter 

    model = calc_model(z) 
    cost_percen = cost(model, data)*100 

    if counter % number_of_param == 0 :
        print(f"run: {counter/number_of_param }. cost = {cost_percen}%")

    cost_array[counter] = cost_percen

    counter +=1 
    return cost_percen


def calc_z_bounds(): #taken directly from 5 col for reproducibility; remove H current params
    
    # input gain -----------------------------
      
    l_z_bound     = 0.1
    h_z_bound     = 100.0
    
    z_bounds = [(l_z_bound,h_z_bound)]
    
    for i in range(num_cells_per_col-1): 
        z_bounds.append((l_z_bound,h_z_bound))

    # output gain ----------------------------
        
    l_z_bound     = 0.1
    h_z_bound     = 100.0
    
    for i in range(num_cells_per_col): 
        z_bounds.append((l_z_bound,h_z_bound))
         
    return z_bounds

z_bounds = calc_z_bounds()   #taken directly from 5 col for reproducibility; remove H current params
    
def create_rand_params():
    
    z = np.zeros(number_of_param)
    
    for i in range(number_of_param):
            
        z_mean  = (z_bounds[i][1]+z_bounds[i][0])/2.0
        z_range = (z_bounds[i][1]-z_bounds[i][0])/2.0
        z[i]    = z_mean+(np.random.rand()-0.5) * z_range
            
    return z


def guess_initial_params(): #taken directly from 5 col for reproducibility 
    
    z = np.zeros(number_of_param)
    
    z[0:65]   = + 0.5    + (np.random.rand(65)-0.5)*0.2
    z[65:130] = + 0.5    + (np.random.rand(65)-0.5)*0.2
    
    return z
    
def calc_z_init(z,init_option):  #taken directly from 5 col for reproducibility 
    
    if init_option == 0:
        z = 1.0 * z   
    if init_option == 1:
        z=guess_initial_params()      
    if init_option == 2:
        z=create_rand_params()
        
    return z

def plot_cost_array(cost):
    
    plt.figure()
    plt.plot(cost)
    plt.yscale('log')

def plot_model(data, model, label1 = 'data', label2 = 'model'):
    
    fontsize_legend = 8
    fontsize_ticklabels = 8
    fontsize_axislabel = 9
    
    mylw = 2
    
    # set x and y position for each cell type
    
    xpos = np.zeros(13)
    ypos = np.zeros(13)
    
    # L1-5
    
    xpos[0:5] = 0.25+np.arange(5)*0.11
    ypos[0:5] = 0.77
    
    # T4-Inputs
    
    xpos[5:9] = 0.06+np.arange(4)*0.11
    ypos[5:9] = 0.27
    
    # T5-Inputs
    
    xpos[9:13] = 0.55+np.arange(4)*0.11
    ypos[9:13] = 0.27
    
    xsize = 0.09
    ysize = 0.15
            
    def set_yticks():
        
        if i == 0 or i == 5 or i == 9:
            plt.yticks(np.arange(7)*10-30,np.arange(7)*10-30,fontsize=fontsize_ticklabels)
        else:
            plt.yticks(np.arange(7)*10-30,'')
            
    ylabelset = set([0,5,9])
            
    plt.figure(figsize=(16,9))
    
    for i in range(13):
                
        # Extract Impulse Responses from xt

        ImpR_model = 1.0*model[i,4]
        
        ImpR_data  = 1.0*data[i,4]
        
        # Extract Receptive field from xt
        
        maxamp_model = np.max(abs(ImpR_model))
        maxamp_data  = np.max(abs(ImpR_data))
        
        maxt_model = np.where(abs(ImpR_model) == np.max(abs(ImpR_model)))[0][0]
        maxt_data  = np.where(abs(ImpR_data)  == np.max(abs(ImpR_data)))[0][0]
        
        RecF_model = bs.rebin(model[i,:,maxt_model],45)
        RecF_model = bs.blurr(RecF_model,5)
        RecF_model = RecF_model/np.max(abs(RecF_model))*maxamp_model
        
        RecF_data  = bs.rebin(data[i,:,maxt_data],45)
        RecF_data  = bs.blurr(RecF_data,5)
        RecF_data  = RecF_data/np.max(abs(RecF_data))*maxamp_data
        
        # --------plotting ---------------------------------------
        
        bs.setmyaxes(xpos[i],ypos[i],xsize,ysize)
        
        plt.plot(np.roll(RecF_data,-2),color='gray',label=label1,linewidth = mylw)
        plt.plot(np.roll(RecF_model,-2),color='red',label=label2,linewidth = mylw)
            
        plt.ylim(-30,30)
        set_yticks()
        
        plt.xlim(0,40)
        
        plt.xticks(np.arange(5)*10,np.arange(5)*10-20,fontsize=fontsize_ticklabels)
        if i in [0,5,9]: plt.legend(loc=1,frameon=False,fontsize=fontsize_legend)
        plt.title(cell_list[i])
            
        plt.xlabel('visual angle [deg]',fontsize=fontsize_axislabel)
        
        if i in ylabelset: plt.ylabel('response [mV]')
                
        bs.setmyaxes(xpos[i],ypos[i]-0.20,xsize,ysize)
        
        plt.plot(ImpR_data,color='gray',label=label1,linewidth = mylw)
        plt.plot(ImpR_model,color='red',label=label2,linewidth = mylw)
        
        cost = np.sum((ImpR_model - ImpR_data)**2)/np.sum((ImpR_data)**2)
        match = int(100*(1-cost))
        
        plt.text(95,-26,'match: ' + str(match) + ' %',fontsize=fontsize_legend)
            
        plt.ylim(-30,30)
        set_yticks()
        
        plt.xlim(0,200)
        
        plt.xticks(np.arange(5)*50,np.arange(5)*0.5,fontsize=fontsize_ticklabels)
            
        plt.xlabel('time [s]',fontsize=fontsize_axislabel)
        if i in ylabelset: plt.ylabel('response [mV]')
        
        if i == 0:
            plt.text(530,130,'Lamina',fontsize=14)
            
        if i == 5:
            plt.text(405,130,'T4 Input',fontsize=14)
            
        if i == 9:
            plt.text(405,130,'T5 Input',fontsize=14)
        
        plt.pause(0.1)

def plot_params(z,all_cells = 0,mytitle =''):
    
    plt.figure(figsize=(7,11))
    
    fontsize_legend = 8
    xpos = -20
    mylw = 3
    
    if all_cells == 1:
        
        plot_index = np.arange(nofcells)
        plot_list  = ctype
        
    else:
            
        plot_index = cell_index
        plot_list  = cell_list
        
    max_num = plot_index.shape[0]
    
    my_cmap = plt.get_cmap("viridis")
    
    for i in range(2):
    
        plt.subplot(3,1,i+1)
        
        plt.bar(np.arange(max_num),z[plot_index+i*65],color=my_cmap(np.arange(max_num)/(1.0*max_num)))
        
        if all_cells == 0:
            
            plt.xticks(np.arange(max_num),plot_list)
            
        else:
            
            plt.xticks(np.arange(max_num),plot_list,rotation='vertical',fontsize=6)    
        
        if i == 0: 
            
            plt.ylabel('input gain')
            plt.title(mytitle)
            
        if i == 1: plt.ylabel('output gain')
        
        plt.yscale('log')
        plt.ylim(0.05,500)
    
    plt.subplot(3,1,3)
    
    Ih_gmax  = z[130:135]
    Ih_midv  = z[135]
    Ih_slope = z[136]
    tau_midv = z[137]
    
    Vm       = np.arange(100)-100
    Ih_ss    = 1.0/(1.0+np.exp((Ih_midv-Vm)*Ih_slope))
    tau      = 1.5/(np.exp(-0.1*(Vm-tau_midv))+np.exp(+0.1*(Vm-tau_midv)))+0.1
    
    plt.plot(Vm,Ih_ss,label = 'Ih Activation',linewidth=mylw)
    plt.plot(Vm,tau,  label = 'Ih time constant [s]',linewidth=mylw)
    plt.xlabel('membrane potential [mV]')
    plt.legend(loc=1,frameon=False, fontsize = fontsize_legend)
    
    plt.text(xpos,0.7,'Ih_midv  = ' +str(int(Ih_midv*100)/100.0),fontsize = fontsize_legend)
    plt.text(xpos,0.6,'Ih_slope = ' +str(int(Ih_slope*100)/100.0),fontsize = fontsize_legend)
    plt.text(xpos,0.5,'tau_midv = ' +str(int(tau_midv*100)/100.0),fontsize = fontsize_legend)
    
    bs.setmyaxes(0.2,0.2,0.2,0.1)
    plt.bar(np.arange(5),Ih_gmax)
    plt.xticks(np.arange(5),['L1','L2','L3','L4','L5'],fontsize = fontsize_legend)
    plt.yticks(np.arange(5)*20,np.arange(5)*20,fontsize = fontsize_legend)
    plt.title('Ih_gmax',fontsize = fontsize_legend)

def send_message(res,a,b):
    
    run_time = (b-a)/60.0
    
    print()
    print('Optimization Success  :', res.success)
    print('Last Value of cost fct:', format(res.fun,'.2f'))
    print('Number of cost fct use:', res.nfev)
    print('total run time        :', format(run_time, '.2f'), ' min')
    print()

def fit_params(z, init_option, plotit=1):  # final model?

    z = calc_z_init(z, init_option)
    model = calc_model(z)

    global counter

    a = time.time()
    counter = 0
    z_init = calc_z_init(z, init_option)
    options = {'maxiter': max_iter * number_of_param}

    res = minimize(calc_cost, z_init, method='L-BFGS-B', tol=1e-8, bounds=z_bounds, options=options)

    z = res.x

    b = time.time()

    print("done!")

    final_fitted_model = calc_model(z)
    fitted_final_model = final_fitted_model

    if plotit == 1:
        # plot_cost_array(cost_array[0:counter])
        # plot_model(data, calc_model(z))
        # plot_params(z)
        pass

    return z, fitted_final_model












