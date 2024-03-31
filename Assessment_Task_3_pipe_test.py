# %%
import pandas as pd
import math
import glob
import os
import datetime as dt
import matplotlib.pyplot as plt

# %% [markdown]
# # inputs

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
measurements = list_files(input_dir, 'pipe_test*.csv', 'file_path')
measurements['file_name'] = measurements.file_path. str.split(pat='/').str[-1]
print('='*20, measurements, '-'*10, '\n', sep='\n')

# %% [markdown]
# # friction factor vs Reynold's number

# %%
theoretical_values = pd.read_csv(filepath_or_buffer='./Inputs_Assessment_Task_3_Laboratory_Report/theoretical_values.csv')
theoretical_values['friction_factor'] = theoretical_values.apply(
    lambda arg: 64/arg.reynolds_number if arg.reynolds_number else 0.316*(arg.reynolds_number**-0.25), axis=1)
theoretical_values.to_csv(path_or_buf='{}friction_factor_vs_reynolds_number.csv'.format(output_dir), index=False)
print('='*20, theoretical_values, '-'*10, '\n', sep='\n')

# %%
fig, ax = plt.subplots(figsize=(10,6))
ax.plot(theoretical_values.reynolds_number.to_numpy(), theoretical_values.friction_factor.to_numpy(), '-o', label='theoretical')
ax.plot([2300,2300], [0, 1])
ax.plot([4000,4000], [0, 1])
ax.legend()
ax.grid(visible=True, which='both')
ax.set_xscale(value='log')
ax.set_yscale(value='log')
ax.set_title(label='friction factor vs reynolds_number\nf vs Re')
ax.set_xlabel(xlabel='Reynold\'s number ($R_e$)')
ax.set_ylabel(ylabel='friction factor ($f$)')
ax.annotate(text='turbulent', xy=(10000, 0.2), xytext=(0, 0), textcoords='offset points')
ax.annotate(text='transitional', xy=(2200, 0.35), xytext=(0, 0), textcoords='offset points')
ax.annotate(text='laminar', xy=(500, 0.5), xytext=(0, 0), textcoords='offset points')
fig.savefig(fname='{}friction_factor_vs_reynolds_number.png'.format(output_dir))
ax.cla()
fig.clf()
plt.close(fig=fig)

# %% [markdown]
# # water kinematic viscosity

# %%
water_kinematic_viscosity = pd.read_csv(filepath_or_buffer='./Inputs_Assessment_Task_3_Laboratory_Report/water_kinematic_viscosity.csv')
water_kinematic_viscosity.kinematic_viscosity = water_kinematic_viscosity.kinematic_viscosity*(10**-6)
water_kinematic_viscosity.to_csv(path_or_buf='{}water_kinematic_viscosity_vs_temperature.csv'.format(output_dir))
print('='*20, water_kinematic_viscosity, '-'*10, '\n', sep='\n')

# %%
fig, ax = plt.subplots(figsize=(15,8))
ax.plot(water_kinematic_viscosity.temperature.to_numpy(), water_kinematic_viscosity.kinematic_viscosity.to_numpy(), '-o', label='kinematic_viscosity')
ax.grid(visible=True, which='both')
ax.set_title(label='Kinematic Viscosity vs Temperature\n\u03BD vs T')
ax.set_xlabel(xlabel='Temperature (\N{DEGREE SIGN}C)')
ax.set_ylabel(ylabel='Kinematic Viscosity ($10^{-6} m^2/s$)')
fig.savefig(fname='{}water_kinematic_viscosity_vs_temperature.png'.format(output_dir))
ax.cla()
fig.clf()
plt.close(fig=fig)

# %% [markdown]
# # pipe properties

# %%
diameter = 0.003
length = 0.5
print('='*20, 'diameter: {}m'.format(diameter), 'length: {}m'.format(length), '-'*10, '\n', sep='\n')

# %% [markdown]
# # calculations

# %%
def calculations(arg_file_path, arg_file_name, arg_output_dir=output_dir, arg_viscosity=water_kinematic_viscosity, arg_diameter=diameter, arg_length=length):

    # raw data
    test = pd.read_csv(filepath_or_buffer=arg_file_path)
    test, temperature = test.iloc[:,:-1], test.iloc[:,-1].dropna()[0]
    kinematic_viscosity = arg_viscosity[arg_viscosity.temperature == temperature].iloc[0,1]
    print(
        '='*20, arg_file_name, '-'*10, 'raw data', '-'*10,
        'Temperature: {}\N{DEGREE SIGN}C'.format(temperature),
        'Kinematic Viscosity: {} m^2/s'.format(kinematic_viscosity),
        '-'*10, test, '\n', sep='\n'
        )

    # SI units
    test.h1 = test.h1/1000
    test.h2 = test.h2/1000
    test['hl'] = test.h2 - test.h1
    test.volume = test.volume/1000
    test.time = pd.to_timedelta('00:' + test.time.astype(str))/dt.timedelta(seconds=1)
    test = test[test.columns[[0,1,2,5,3,4]]]
    test.to_csv(path_or_buf='{}SI_units_{}'.format(arg_output_dir, arg_file_name), index=False)
    print('-'*10, 'SI units data', '-'*10, test, '\n', sep='\n')

    # calculations
    test.rename(columns={'hl':'head_loss'}, inplace=True)
    test['discharge'] = (test.volume/test.time)/1000
    test['velocity'] = test.discharge/(math.pi*(arg_diameter**2)/4)
    test['friction_factor'] = test.head_loss*arg_diameter*(2*9.81)/(arg_length*(test.velocity**2))
    test['reynolds_number'] = test.velocity*arg_diameter/kinematic_viscosity
    test = test[test.columns[[0,3,4,5,6,7,8,9]]]
    test.to_csv(path_or_buf='{}calculations_{}'.format(arg_output_dir, arg_file_name), index=False)
    print('-'*10, 'calculations', '-'*10, test, '\n', sep='\n')

    # plot
    fig, ax = plt.subplots(figsize=(10,6))
    ax.plot(test.reynolds_number.to_numpy(), test.friction_factor.to_numpy(), '-o', label='experimental')
    ax.plot(theoretical_values.reynolds_number.to_numpy(), theoretical_values.friction_factor.to_numpy(), '-o', label='theoretical')
    ax.plot([2300,2300], [0, 1])
    ax.plot([4000,4000], [0, 1])
    ax.legend()
    ax.set_xscale(value='log')
    ax.set_yscale(value='log')
    ax.grid(visible=True, which='both')
    ax.set_title(label='Friction Factor vs Reynold\'s Number\n$f$ vs $R_e$\n{}'.format(arg_file_name.split(sep='.')[0]))
    ax.set_xlabel(xlabel='Reynold\'s number ($R_e$)')
    ax.set_ylabel(ylabel='friction factor ($f$)')
    ax.annotate(text='turbulent', xy=(10000, 0.2), xytext=(0, 0), textcoords='offset points')
    ax.annotate(text='transitional', xy=(2200, 0.35), xytext=(0, 0), textcoords='offset points')
    ax.annotate(text='laminar', xy=(500, 0.5), xytext=(0, 0), textcoords='offset points')
    fig.savefig(fname='{}Plot_friction_factor_vs_reynolds_number_{}.png'.format(arg_output_dir, arg_file_name.split(sep='.')[0]))
    ax.cla()
    fig.clf()
    plt.close(fig=fig)

    # plot
    fig, ax = plt.subplots(figsize=(10,6))
    ax.plot(test.velocity.to_numpy(), test.head_loss.to_numpy(), '-o', label='experimental')
    ax.legend()
    ax.set_xscale(value='log')
    ax.set_yscale(value='log')
    ax.grid(visible=True, which='both')
    ax.set_title(label='Head Loss vs Velocity\n$HL$ vs $v$\n{}'.format(arg_file_name.split(sep='.')[0]))
    ax.set_xlabel(xlabel='velocity ($v$ in $m/s$)')
    ax.set_ylabel(ylabel='head loss ($HL$ in $m$)')
    fig.savefig(fname='{}Plot_head_loss_vs_velocity_{}.png'.format(arg_output_dir, arg_file_name.split(sep='.')[0]))
    ax.cla()
    fig.clf()
    plt.close(fig=fig)

# %%
measurements.apply(func=lambda arg: calculations(arg.file_path, arg.file_name), axis=1)

# %%



