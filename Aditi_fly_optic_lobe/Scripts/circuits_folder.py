import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
import blindschleiche_py3 as bs
from scipy.signal import chirp


dir_name = "Aditi_fly_optic_lobe"
output_dir = dir_name + "/circuits"
central_file_loc = dir_name + "/data/central_column_connectivity.csv"
offset_file_loc = dir_name + "/data/offset_column_connectivity.csv"


MATRIX_CELL_NUM = 65
NUM_COLS = 5 
CELL_LIST = np.array(['L1','L2','L3','L4','L5','Mi1','Tm3','Mi4','Mi9','Tm1','Tm2','Tm4','Tm9'])
NUM_CELLS_TEST = len(CELL_LIST)


#save header 
def c_type(f_path, output_path) : 
     df = pd.read_csv(f_path, header=0, index_col=0) #drops header and first col giving 65x65 matrix
     output = df.index.to_numpy().astype(str) #need to cast to string bc of a "pickle" issue
     print(output) #should print array of cell names 
     #save file 
     np.save(output_path, output) #np save takes file path first, output second! 


#write general function that takes file and creates a 65 x 65 matrix with same values as in the csv 

def single_conM(f_path, output_path) :

    #load file 
    df = pd.read_csv(f_path, header=0, index_col=0) #drops header and first col giving 65x65 matrix
    df = df.fillna(0)  #fill empty cells with 0s
    output = df.to_numpy() #convert to numpy array 

    print(df.loc['R1', 'L1']) #should give -40 for intra and 0 for inter 
   
    #save file 
    np.save(output_path,output.transpose())  #transpose numpy for the future -> in simulation 



#saving csv files as numpy arrays 

output_dir_central = output_dir + "/intra_colM_rec.npy"
output_dir_offset = output_dir + "/inter_colM_rec.npy"
output_dir_c_type = output_dir + "/c_type_rec.npy"

single_conM(central_file_loc, output_dir_central)
single_conM(offset_file_loc, output_dir_offset)
c_type(central_file_loc,output_dir_c_type)


C_TYPE = np.load(output_dir + "/c_type_rec.npy") #array of 65 cells 

#function : given cell name, returns position in c_type array 

def one_cell_pos(cell_name) : 
     
    for i in range(len(C_TYPE)) :  #len returns number in array; range creates an array of numbers to iterate through 0-number
          
          if cell_name == C_TYPE[i] :  
            return i
          
    raise KeyError(f" '{cell_name}' not found in C_TYPE") #return vs raise: raise error vs return something in function 
          
def find_pos_from_cell_list() :

    arr = np.zeros(NUM_CELLS_TEST)

    for i in range(NUM_CELLS_TEST) :  # i in arr would iterate through each value within arr array which would be 0.0.... need to iterate through 0-12 which would be range(num_Cells)

        arr[i] = one_cell_pos(CELL_LIST[i])

    return arr 

def create_mc_cell_list(output_dir) :
    
    arr = np.zeros(NUM_CELLS_TEST*NUM_COLS) #creates 65 array 
    cell_arr = find_pos_from_cell_list() # 13 array with each value a 
    print(cell_arr)

    start_pos = 0
    end_pos = 13 

            
    for i in range(NUM_COLS) : 

        new_pos = cell_arr + i*65 
        new_start_pos = start_pos + i*13
        new_end_pos = end_pos + i*13 

        arr[new_start_pos : new_end_pos] = new_pos


    print(arr)
    np.save(output_dir, arr.astype(int)) 


output_dir_mc_cell_list = output_dir + "/mc_cell_index_rec.npy"
create_mc_cell_list(output_dir_mc_cell_list)


#create multi-col index 
def create_multi_colM(output_dir) :

    #initialize zeroes matrix + load in prev matrix
    multicolM = np.zeros((NUM_COLS*MATRIX_CELL_NUM, NUM_COLS*MATRIX_CELL_NUM)) #325 X 325 array 
    intracolM = np.load(output_dir_central) #intracolM
    intercolM = np.load(output_dir_offset) #inter
    
    #for inter it will be the same; you add 65 per column 
    start_pos = 0 #inclusive in arrays 
    end_pos = 65 #exclusive in arrays 

    for i in range(NUM_COLS):
        new_start_pos = start_pos + 65*i
        new_end_pos = end_pos + 65*i
        multicolM[new_start_pos:new_end_pos, new_start_pos:new_end_pos] = intracolM

        if i == 4 : 
            break  #break vs continue : break exits loop entirely continue skips rest of loop and starts over with different iteration 

        inter_colM_start_pos = new_start_pos + 65
        inter_colM_end_pos = new_end_pos + 65
        
        #case for adding col (right of diagnonal)
        multicolM[new_start_pos:new_end_pos, inter_colM_start_pos:inter_colM_end_pos] = intercolM/2 
        #case for adding rows (below diagnoal)
        multicolM[inter_colM_start_pos:inter_colM_end_pos, new_start_pos:new_end_pos]= intercolM/2 

        
    np.save(output_dir, multicolM) 


output_dir_multicolM = output_dir + "/multi_colM_rec.npy"
create_multi_colM(output_dir_multicolM)  


#graph all different connectivity matrixes 


def plot_figure2() : 

    intracolM = np.load(output_dir_central) #intracolM
    intercolM = np.load(output_dir_offset) #inter
    multicolM = np.load(output_dir_multicolM) #multicolM 
    output_dir = dir_name + "/Results"

    arr = [intracolM, intercolM, multicolM] 
    titles = ["intracolumn_connectivity", "intercolumn_connectivity", "overall_connectivity"]

    for i in range(len(arr)) : 

        plt.figure(figsize=(12, 12))
        plt.imshow(arr[i], cmap='coolwarm', vmin=-10, vmax=10)

        if i != 2 : 

            plt.xticks(np.arange(65), C_TYPE,  rotation = 90, fontsize = 5)
            plt.yticks(np.arange(65), C_TYPE, rotation = 0, fontsize = 5)
        
        plt.colorbar()
        plt.title(f"{titles[i]}")
       
        final_output = output_dir + f"/{titles[i]}.png"
        plt.savefig(final_output)
        plt.show()

    
plot_figure2()