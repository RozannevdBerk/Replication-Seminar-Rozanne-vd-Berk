import pandas as pd
import threading
import random
from datetime import datetime,timedelta
import time

# region Creating event data based on extended process
df_lock = threading.Lock()
FS_lock = threading.Lock()
SS_lock = threading.Lock()

event_df = pd.DataFrame(columns=['eventId','activity','timestamp','timestampVar','box','batchPosition','equipment','log'])

boxprocess = ['LoadFS','Open','Fill','UnloadFS','LoadSS','Close','Seal','UnloadSS']


def write_boxprocess_to_df(bid:str, batchpos:str, eq:int):
    '''
    :param bid: box identifier (bx, with x as a number)
    :param eq: equipment
    :param batchpos: batchPosition (x, y, or z)

    Write boxprocess for a single box to dataframe
    '''
    global event_df
    with FS_lock: #to indicate that the Filling Station is currently in use
        for act in boxprocess[:4]:
            if act in ['LoadFS','UnloadFS']:
                with df_lock:
                    event_df.loc[len(event_df),['activity','batchPosition','equipment']] = [act,batchpos,eq]
            else:
                with df_lock:
                    event_df.loc[len(event_df),['activity','equipment']] = [act,eq]

    with SS_lock: #to indicate that the Sealing Station is currently in use
        for act in boxprocess[4:]:
            if act == 'Seal':
                with df_lock:
                    event_df.loc[len(event_df),['activity','box','equipment']] = [act,bid,eq]
            elif act == 'Close':
                with df_lock:
                    event_df.loc[len(event_df),['activity','equipment']] = [act,eq]
            else:
                with df_lock:
                    event_df.loc[len(event_df),['activity','batchPosition','equipment']] = [act,batchpos,eq]



i = 1
batchpos = ['x','y','z']
while i<1000:
    equipment = random.choice([1012,2012,3012,4012,5012,6012,7012,8012,9012,1465,2465,3465,4465,5465,6465,7465,8465,9465])
    event_df.loc[len(event_df),['activity','equipment']] = ['LoadAL',equipment]
    random.shuffle(batchpos)

    t1 = threading.Thread(target=write_boxprocess_to_df, args=[f'b{i}',batchpos[0],equipment])
    t2 = threading.Thread(target=write_boxprocess_to_df, args=[f'b{i+1}',batchpos[1],equipment])
    t3 = threading.Thread(target=write_boxprocess_to_df, args=[f'b{i+2}',batchpos[2],equipment])

    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()

    event_df.loc[len(event_df),['activity','equipment']] = ['UnloadAL',equipment]
    i += 3

event_df.loc[:,'log'] = 'ExtendedExample'
event_df.loc[:,'timestamp'] = [datetime(year=2023,month=10,day=31,hour=10)+timedelta(seconds=t) for t in range(len(event_df))]
event_df.loc[:,'timestamp'] = event_df['timestamp'].dt.strftime('%d/%m/%Y %H:%M:%S')
event_df.loc[:,'timestampVar'] = [f't{i}' for i in range(1,len(event_df)+1)]
event_df.loc[:,'eventId'] = [f'e{i}' for i in range(1,len(event_df)+1)]

event_df.to_csv('./box_process_data/event_data_extended.csv', header=True, index=True, index_label='idx')

# endregion

