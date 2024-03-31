# %%
import pandas as pd
import glob
import os
import matplotlib.pyplot as plt

# %% [markdown]
# # Inputs

# %%
input_dir = './Inputs_Assessment_Task_3_Laboratory_Report/'
output_dir = './Outputs_Assessment_Task_3_Laboratory_Report/'

print(
    '='*20, 
    input_dir,
    output_dir,
    '-'*10, '\n', 
    sep='\n'
    )

# %% [markdown]
# # create output directory

# %%
def create_output_dir(arg_output_dir):
    """create output directory if it does not exist

    arguments:
        [string] --> arg_output_dir = path of the output directory name
    """
    if not os.path.exists(arg_output_dir):
        os.makedirs(arg_output_dir)

# %%
create_output_dir(output_dir)
print('='*20, output_dir, '-'*10, '\n', sep='\n')

# %% [markdown]
# # Bernoulli apparatus properties

# %%
dist = pd.Series(data=[0, 0.06028, 0.06868, 0.07318, 0.08108, 0.14154],name='dist')
area = pd.Series(data=[0.00049, 0.00015, 0.00011, 0.00009, 0.000079, 0.00049], name='area')
bernoulli_aparatus = pd.concat([dist, area], axis=1)
print('='*20, bernoulli_aparatus, '-'*10, '\n', sep='\n')

# %% [markdown]
# # read files

# %%
def list_files(arg_directory_path, arg_regex, arg_column_name='file_path'):
    """return list of files in a directory

    arguments:
        [string] --> arg_directory_path = directory path of the polygons
        [string] --> arg_regex = regex entry
        [string] --> arg_column_name = column's name
    """
    list_files = glob.glob(pathname=arg_directory_path + arg_regex)
    list_files = pd.DataFrame(list_files, columns=[arg_column_name])
    list_files.sort_values(by=[arg_column_name], inplace=True)
    list_files.reset_index(drop=True, inplace=True)

    return list_files

# %%
measurements = list_files(input_dir, 'bernoulli*.csv', 'file_path')
measurements['file_name'] = measurements.file_path. str.split(pat='/').str[-1]
print('='*20, measurements, '-'*10, '\n', sep='\n')

# %% [markdown]
# # Calculation and graphs

# %%
def calculations(arg_file_path, arg_file_name, arg_output_dir=output_dir, arg_dist=dist, arg_area=area):

    # raw data
    test = pd.read_csv(filepath_or_buffer=arg_file_path)
    print('='*20, arg_file_name, '-'*10, 'raw data', '-'*10, test, '\n', sep='\n')

    # SI units
    test['dist'] = arg_dist
    test['area'] = arg_area
    test['flow_rate'] = (test.volume/1000000)/test.time
    test['velocity'] = test.flow_rate/test.area
    test['pressure_head'] = test.static_head/1000
    test['velocity_head'] = (test.velocity**2)/(2*9.81)
    test['calculated_total_head'] = test.pressure_head + test.velocity_head
    test['measured_total_head'] = test.total_head/1000
    test = test[test.columns[[0,5,6,7,8,9,10,11,12]]]
    test.to_csv(path_or_buf='{}SI_units_{}'.format(arg_output_dir, arg_file_name), index=False)
    print('='*20, arg_file_name, '-'*10, 'SI units data', '-'*10, test, '\n', sep='\n')

    # plot
    fig, ax = plt.subplots(figsize=(10,6))
    ax.plot(
        test.dist.to_numpy(),
        test.pressure_head.to_numpy(),
        '-o',
        label='pressure head'
        )
    ax.plot(
        test.dist.to_numpy(),
        test.velocity_head.to_numpy(),
        '-o',
        label='velocity head'
        )
    ax.plot(
        test.dist.to_numpy(),
        test.calculated_total_head.to_numpy(),
        '-o',
        label='calculated total head'
        )
    ax.plot(
        test.dist.to_numpy(),
        test.measured_total_head.to_numpy(),
        '-o',
        label='measured total head'
        )
    
    ax.legend()
    ax.grid(visible=True, which='both')
    ax.set_title(label='Pressure vs Distance\n{}'.format(arg_file_name.split(sep='.')[0]))
    ax.set_xlabel(xlabel='Distance in ($m$)')
    ax.set_ylabel(ylabel='Pressure in height ($m$)')
    fig.savefig(fname='{}Plot_{}.png'.format(arg_output_dir, arg_file_name.split(sep='.')[0]))
    ax.cla()
    fig.clf()
    plt.close(fig=fig)

# %%
measurements.apply(func=lambda arg: calculations(arg.file_path, arg.file_name), axis=1)

# %%



