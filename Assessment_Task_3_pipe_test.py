# %%
import pandas as pd
import numpy as np
import math
import glob
import os
import traceback
import datetime as dt
import matplotlib.pyplot as plt

# %%
def create_output_dir(arg_output_dir):
    """create output directory if it does not exist

    arguments:
        [string] --> arg_output_dir = path of the output directory name
    """
    if not os.path.exists(arg_output_dir):
        os.makedirs(arg_output_dir)

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
def calculations(
        arg_file_path, arg_file_name, arg_output_dir, 
        arg_viscosity, arg_diameter, arg_length, arg_theoretical_values
    ):

    # raw data
    test = pd.read_csv(filepath_or_buffer=arg_file_path)
    test, temperature = (
        test.iloc[:,:-1], 
        test.iloc[:,-1].dropna().iloc[0]
    )
    # kinematic_viscosity = arg_viscosity[arg_viscosity.temperature == temperature].iloc[0,1]
    kinematic_viscosity = np.interp(
        x=temperature, 
        xp=arg_viscosity.temperature.to_numpy(), 
        fp=arg_viscosity.kinematic_viscosity.to_numpy()
    )
    print(
        '-'*80, '',
        f'# {arg_file_name}', '',
        '## raw data', '',
        'Temperature: {}\N{DEGREE SIGN}C'.format(temperature),
        'Kinematic Viscosity: {} m^2/s'.format(kinematic_viscosity), '',
        test.to_markdown(index=False), '',
        sep='\n'
    )

    # SI units
    test.h1 = test.h1/1000
    test.h2 = test.h2/1000
    test['hl'] = (test.h2 - test.h1).abs()
    test.sort_values(by=['hl'], inplace=True)
    test.volume = test.volume/1000
    # test.time = pd.to_timedelta('00:' + test.time.astype(str))/dt.timedelta(seconds=1)
    test.time = pd.to_numeric(test.time)
    test = test[test.columns[[0,1,2,5,3,4]]]
    test.to_csv(path_or_buf='{}SI_units_{}'.format(arg_output_dir, arg_file_name), index=False)
    print(
        '## SI units data', '',
        test.to_markdown(index=False), '',
        sep='\n'
    )

    # calculations
    test.rename(columns={'hl':'head_loss'}, inplace=True)
    test['discharge'] = (test.volume/test.time)/1000
    test['velocity'] = test.discharge/(math.pi*(arg_diameter**2)/4)
    # test['friction_factor'] = test.head_loss*arg_diameter*(2*9.81)/(arg_length*(test.velocity**2))
    test['friction_factor'] = np.where(
        test.velocity > 0,
        (
            test.head_loss
            * arg_diameter
            * (2 * 9.81)
            / (arg_length * (test.velocity ** 2))
        ),
        np.nan
    )
    test['reynolds_number'] = test.velocity*arg_diameter/kinematic_viscosity
    test = test[test.columns[[0,3,4,5,6,7,8,9]]]
    test.to_csv(path_or_buf='{}calculations_{}'.format(arg_output_dir, arg_file_name), index=False)
    print(
        '## calculations', '',
        test.to_markdown(index=False), '',
        sep='\n'
    )
    valid = (
        (test.reynolds_number > 0)
        & (test.friction_factor > 0)
        & np.isfinite(test.reynolds_number)
        & np.isfinite(test.friction_factor)
    )

    # plot
    fig, ax = plt.subplots(figsize=(10,6))
    # ax.plot(test.reynolds_number.to_numpy(), test.friction_factor.to_numpy(), '-o', label='experimental')
    ax.plot(
        test.loc[valid, 'reynolds_number'],
        test.loc[valid, 'friction_factor'],
        '-o',
        label='experimental'
    )
    ax.plot(
        arg_theoretical_values.reynolds_number.to_numpy(), 
        arg_theoretical_values.friction_factor.to_numpy(), 
        '-o', label='theoretical'
    )
    ax.axvline(x=2300)
    ax.axvline(x=4000)
    for ind1, ind2, ind3 in zip(
        # np.arange(start=1, stop=len(test)+1), 
        test.index.to_numpy(),
        test.reynolds_number.to_numpy(), 
        test.friction_factor.to_numpy()
    ):
        ax.annotate(text=ind1+1, xy=(ind2, ind3), xytext=(0, 5), textcoords='offset points', fontsize=8)
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
    fname='{}Plot_friction_factor_vs_reynolds_number_{}.png'.format(
        arg_output_dir, 
        arg_file_name.split(sep='.')[0]
    )
    fig.savefig(fname=fname)
    ax.cla()
    fig.clf()
    plt.close(fig=fig)

    print(f'![Plot]({fname})')
    print()

    # plot
    fig, ax = plt.subplots(figsize=(10,6))
    ax.plot(
        # test.velocity.to_numpy(), 
        # test.head_loss.to_numpy(), 
        test.loc[valid, 'velocity'],
        test.loc[valid, 'head_loss'],
        '-o', 
        label='experimental'
    )
    for ind1, ind2, ind3 in zip(
        # np.arange(start=1, stop=len(test)+1), 
        test.index.to_numpy(),
        test.velocity.to_numpy(), 
        test.head_loss.to_numpy()
    ):
        ax.annotate(text=ind1+1, xy=(ind2, ind3), xytext=(0, 5), textcoords='offset points', fontsize=8)
    ax.legend()
    ax.set_xscale(value='log')
    ax.set_yscale(value='log')
    ax.grid(visible=True, which='both')
    ax.set_title(label='Head Loss vs Velocity\n$HL$ vs $v$\n{}'.format(arg_file_name.split(sep='.')[0]))
    ax.set_xlabel(xlabel='velocity ($v$ in $m/s$)')
    ax.set_ylabel(ylabel='head loss ($HL$ in $m$)')
    fname = '{}Plot_head_loss_vs_velocity_{}.png'.format(
        arg_output_dir, 
        arg_file_name.split(sep='.')[0]
    )
    fig.savefig(fname=fname)
    ax.cla()
    fig.clf()
    plt.close(fig=fig)

    print(f'![Plot]({fname})')
    print()

# %%
def main(input_dir, output_dir):

    print(
        '-'*80, '',
        '# Inputs & Outputs', '',
        f'src: {input_dir}',
        f'dst: {output_dir}', '',
        sep='\n'
        )

# %% [markdown]
# # create output directory

    create_output_dir(output_dir)
    # print('='*20, output_dir, '-'*10, '\n', sep='\n')

# %% [markdown]
# # read files

    measurements = list_files(input_dir, 'pipe_test*.csv', 'file_path')
    measurements['file_name'] = measurements.file_path. str.split(pat='/').str[-1]
    # print('='*20, measurements, '-'*10, '\n', sep='\n')

# %% [markdown]
# # friction factor vs Reynold's number

    file = './Inputs_Assessment_Task_3_Laboratory_Report/theoretical_values.csv'
    theoretical_values = pd.read_csv(filepath_or_buffer=file)
    theoretical_values['friction_factor'] = theoretical_values.apply(
        lambda arg: \
            64/arg.reynolds_number \
            if arg.reynolds_number < 2300 \
            else 0.316*(arg.reynolds_number**-0.25), axis=1
    )
    theoretical_values.to_csv(
        path_or_buf='{}friction_factor_vs_reynolds_number.csv'.format(output_dir), 
        index=False
    )
    print(
        theoretical_values.to_markdown(index=False), '',
        sep='\n'
    )

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
    fname = '{}friction_factor_vs_reynolds_number.png'.format(output_dir)
    fig.savefig(fname=fname)
    ax.cla()
    fig.clf()
    plt.close(fig=fig)

    print(f'![Plot]({fname})')
    print()

# %% [markdown]
# # water kinematic viscosity

# %%
    water_kinematic_viscosity = pd.read_csv(filepath_or_buffer='./Inputs_Assessment_Task_3_Laboratory_Report/water_kinematic_viscosity.csv')
    water_kinematic_viscosity.kinematic_viscosity = water_kinematic_viscosity.kinematic_viscosity*(10**-6)
    water_kinematic_viscosity.to_csv(path_or_buf='{}water_kinematic_viscosity_vs_temperature.csv'.format(output_dir))
    print(
        water_kinematic_viscosity.to_markdown(index=False), '',
        sep='\n'
    )

# %%
    fig, ax = plt.subplots(figsize=(15,8))
    ax.plot(water_kinematic_viscosity.temperature.to_numpy(), water_kinematic_viscosity.kinematic_viscosity.to_numpy(), '-o', label='kinematic_viscosity')
    ax.grid(visible=True, which='both')
    ax.set_title(label='Kinematic Viscosity vs Temperature\n\u03BD vs T')
    ax.set_xlabel(xlabel='Temperature (\N{DEGREE SIGN}C)')
    ax.set_ylabel(ylabel='Kinematic Viscosity ($10^{-6} m^2/s$)')
    fname='{}water_kinematic_viscosity_vs_temperature.png'.format(output_dir)
    fig.savefig(fname=fname)
    ax.cla()
    fig.clf()
    plt.close(fig=fig)

    print(f'![Plot]({fname})')
    print()

# %% [markdown]
# # pipe properties

# %%
    diameter = 0.003
    length = 0.5
    print(
        'diameter: {}m'.format(diameter), 
        'length: {}m'.format(length), '', 
        sep='\n'
    )

# %% [markdown]
# # calculations

    # measurements.apply(
    #     func=lambda arg: calculations(
    #         arg.file_path, arg.file_name,
    #         arg_output_dir=output_dir,
    #         arg_viscosity=water_kinematic_viscosity,
    #         arg_diameter=diameter,
    #         arg_length=length,
    #         arg_theoretical_values=theoretical_values
    #     ), 
    #     axis=1
    # )
    for _, row in measurements.iterrows():

        try:
            calculations(
                row.file_path,
                row.file_name,
                arg_output_dir=output_dir,
                arg_viscosity=water_kinematic_viscosity,
                arg_diameter=diameter,
                arg_length=length,
                arg_theoretical_values=theoretical_values
            )

        except Exception as error:
            print()
            print('-' * 80)
            print(f'ERROR PROCESSING: {row.file_name}')
            print(f'FILE: {row.file_path}')
            print(f'ERROR TYPE: {type(error).__name__}')
            print(f'ERROR: {error}')
            print('-' * 80)
            traceback.print_exc()
            print('-' * 80)
            print()

            continue

# %%

if __name__ == '__main__':

# %% [markdown]
# # inputs

# %%
    # input_dir = './Inputs_Assessment_Task_3_Laboratory_Report/'
    # output_dir = './Outputs_Assessment_Task_3_Laboratory_Report/'
    input_dir = './inputs/'
    output_dir = './outputs/'

    main(input_dir, output_dir)

