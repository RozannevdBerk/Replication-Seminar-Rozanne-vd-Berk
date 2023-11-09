import pandas as pd
from numpy.random import rand
from numpy import nan

event_df = pd.read_csv('./box_process_data/event_data_extended.csv')

# region Create missing values by replacing each cell's value with NaN with a % probability
random_mask = rand(*event_df.shape)
#1% chance
noisy_df1 = event_df.mask(cond=random_mask<0.01, other=nan)
#5% chance
noisy_df2 = event_df.mask(cond=random_mask<0.05, other=nan)
#10% chance
noisy_df3 = event_df.mask(cond=random_mask<0.1, other=nan)
#20% chance
noisy_df4 = event_df.mask(cond=random_mask<0.2, other=nan)

noisy_df1.to_csv('./box_process_data/event_data_noisy1.csv', header=True, index=False)
noisy_df2.to_csv('./box_process_data/event_data_noisy2.csv', header=True, index=False)
noisy_df3.to_csv('./box_process_data/event_data_noisy3.csv', header=True, index=False)
noisy_df4.to_csv('./box_process_data/event_data_noisy4.csv', header=True, index=False)

# endregion

# region Create missing events by removing each row with a % probability
random_mask = rand(len(event_df))

#1% chance
noisy_df5 = event_df.loc[random_mask>=0.01]
#5% chance
noisy_df6 = event_df.loc[random_mask>=0.05]
#10% chance
noisy_df7 = event_df.loc[random_mask>=0.1]
#20% chance
noisy_df8 = event_df.loc[random_mask>=0.2]

noisy_df5.to_csv('./box_process_data/event_data_noisy5.csv', header=True, index=False)
noisy_df6.to_csv('./box_process_data/event_data_noisy6.csv', header=True, index=False)
noisy_df7.to_csv('./box_process_data/event_data_noisy7.csv', header=True, index=False)
noisy_df8.to_csv('./box_process_data/event_data_noisy8.csv', header=True, index=False)

# endregion