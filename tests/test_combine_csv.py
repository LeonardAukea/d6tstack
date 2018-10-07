"""Run unit tests.

Use this to run tests and understand how tasks.py works.

Example:

    Create directories::

        mkdir -p test-data/input
        mkdir -p test-data/output

    Run tests::

        pytest test_combine.py -s

Notes:

    * this will create sample csv, xls and xlsx files    
    * test_combine_() test the main combine function

"""

from d6tstack.combine_csv import *
from d6tstack.sniffer import CSVSniffer

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import ntpath

import pytest

cfg_fname_base_in = 'test-data/input/test-data-'
cfg_fname_base_out_dir = 'test-data/output'
cfg_fname_base_out = cfg_fname_base_out_dir+'/test-data-'
cnxn_string = 'sqlite:///test-data/db/{}.db'

#************************************************************
# fixtures
#************************************************************
class DebugLogger(object):
    def __init__(self, event):
        pass
        
    def send_log(self, msg, status):
        pass

    def send(self, data):
        pass

logger = DebugLogger('combiner')

# sample data
def create_files_df_clean():
    # create sample data
    df1=pd.DataFrame({'date':pd.date_range('1/1/2011', periods=10), 'sales': 100, 'cost':-80, 'profit':20})
    df2=pd.DataFrame({'date':pd.date_range('2/1/2011', periods=10), 'sales': 200, 'cost':-90, 'profit':200-90})
    df3=pd.DataFrame({'date':pd.date_range('3/1/2011', periods=10), 'sales': 300, 'cost':-100, 'profit':300-100})
#    cfg_col = [ 'date', 'sales','cost','profit']
    
    # return df1[cfg_col], df2[cfg_col], df3[cfg_col]
    return df1, df2, df3

def create_files_df_clean_combine():
    df1,df2,df3 = create_files_df_clean()
    df_all = pd.concat([df1,df2,df3])
    df_all = df_all[df_all.columns].astype(str)
    
    return df_all


def create_files_df_clean_combine_with_filename(fname_list):
    df1, df2, df3 = create_files_df_clean()
    df1['filename'] = os.path.basename(fname_list[0])
    df2['filename'] = os.path.basename(fname_list[1])
    df3['filename'] = os.path.basename(fname_list[2])
    df_all = pd.concat([df1, df2, df3])
    df_all = df_all[df_all.columns].astype(str)

    return df_all


def create_files_df_colmismatch_combine(cfg_col_common):
    df1, df2, df3 = create_files_df_clean()
    df3['profit2']=df3['profit']*2
    if cfg_col_common:
        df_all = pd.concat([df1, df2, df3], join='inner')
    else:
        df_all = pd.concat([df1, df2, df3])
    df_all = df_all[df_all.columns].astype(str)

    return df_all


def create_files_df_colmismatch_combine2(cfg_col_common):
    df1, df2, df3 = create_files_df_clean()
    for i in range(15):
        df3['profit'+str(i)]=df3['profit']*2
    if cfg_col_common:
        df_all = pd.concat([df1, df2, df3], join='inner')
    else:
        df_all = pd.concat([df1, df2, df3])
    df_all = df_all[df_all.columns].astype(str)

    return df_all


# csv standard
@pytest.fixture(scope="module")
def create_files_csv():

    df1,df2,df3 = create_files_df_clean()
    # save files
    cfg_fname = cfg_fname_base_in+'input-csv-clean-%s.csv'
    df1.to_csv(cfg_fname % 'jan',index=False)
    df2.to_csv(cfg_fname % 'feb',index=False)
    df3.to_csv(cfg_fname % 'mar',index=False)

    return [cfg_fname % 'jan',cfg_fname % 'feb',cfg_fname % 'mar']

@pytest.fixture(scope="module")
def create_files_csv_colmismatch():

    df1,df2,df3 = create_files_df_clean()
    df3['profit2']=df3['profit']*2
    # save files
    cfg_fname = cfg_fname_base_in+'input-csv-colmismatch-%s.csv'
    df1.to_csv(cfg_fname % 'jan',index=False)
    df2.to_csv(cfg_fname % 'feb',index=False)
    df3.to_csv(cfg_fname % 'mar',index=False)

    return [cfg_fname % 'jan',cfg_fname % 'feb',cfg_fname % 'mar']

@pytest.fixture(scope="module")
def create_files_csv_colmismatch2():

    df1,df2,df3 = create_files_df_clean()
    for i in range(15):
        df3['profit'+str(i)]=df3['profit']*2
    # save files
    cfg_fname = cfg_fname_base_in+'input-csv-colmismatch2-%s.csv'
    df1.to_csv(cfg_fname % 'jan',index=False)
    df2.to_csv(cfg_fname % 'feb',index=False)
    df3.to_csv(cfg_fname % 'mar',index=False)

    return [cfg_fname % 'jan',cfg_fname % 'feb',cfg_fname % 'mar']

@pytest.fixture(scope="module")
def create_files_csv_colreorder():

    df1,df2,df3 = create_files_df_clean()
    cfg_col = [ 'date', 'sales','cost','profit']
    cfg_col2 = [ 'date', 'sales','profit','cost']
    
    # return df1[cfg_col], df2[cfg_col], df3[cfg_col]
    # save files
    cfg_fname = cfg_fname_base_in+'input-csv-reorder-%s.csv'
    df1[cfg_col].to_csv(cfg_fname % 'jan',index=False)
    df2[cfg_col].to_csv(cfg_fname % 'feb',index=False)
    df3[cfg_col2].to_csv(cfg_fname % 'mar',index=False)

    return [cfg_fname % 'jan',cfg_fname % 'feb',cfg_fname % 'mar']

@pytest.fixture(scope="module")
def create_files_csv_noheader():

    df1,df2,df3 = create_files_df_clean()
    # save files
    cfg_fname = cfg_fname_base_in+'input-noheader-csv-%s.csv'
    df1.to_csv(cfg_fname % 'jan',index=False, header=False)
    df2.to_csv(cfg_fname % 'feb',index=False, header=False)
    df3.to_csv(cfg_fname % 'mar',index=False, header=False)

    return [cfg_fname % 'jan',cfg_fname % 'feb',cfg_fname % 'mar']

@pytest.fixture(scope="module")
def create_files_csv_col_renamed():

    df1, df2, df3 = create_files_df_clean()
    df3 = df3.rename(columns={'sales':'revenue'})
    cfg_col = ['date', 'sales', 'profit', 'cost']
    cfg_col2 = ['date', 'revenue', 'profit', 'cost']

    cfg_fname = cfg_fname_base_in + 'input-csv-renamed-%s.csv'
    df1[cfg_col].to_csv(cfg_fname % 'jan', index=False)
    df2[cfg_col].to_csv(cfg_fname % 'feb', index=False)
    df3[cfg_col2].to_csv(cfg_fname % 'mar', index=False)

    return [cfg_fname % 'jan', cfg_fname % 'feb', cfg_fname % 'mar']


def create_files_csv_dirty(cfg_sep=",", cfg_header=True):

    df1,df2,df3 = create_files_df_clean()
    df1.to_csv(cfg_fname_base_in+'debug.csv',index=False, sep=cfg_sep, header=cfg_header)

    return cfg_fname_base_in+'debug.csv'

# excel single-tab
def create_files_xls_single_helper(cfg_fname):
    df1,df2,df3 = create_files_df_clean()
    df1.to_excel(cfg_fname % 'jan',index=False)
    df2.to_excel(cfg_fname % 'feb',index=False)
    df3.to_excel(cfg_fname % 'mar',index=False)

    return [cfg_fname % 'jan',cfg_fname % 'feb',cfg_fname % 'mar']

@pytest.fixture(scope="module")
def create_files_xls_single():
    return create_files_xls_single_helper(cfg_fname_base_in+'input-xls-sing-%s.xls')

@pytest.fixture(scope="module")
def create_files_xlsx_single():
    return create_files_xls_single_helper(cfg_fname_base_in+'input-xls-sing-%s.xlsx')


def write_file_xls(dfg, fname, startrow=0,startcol=0):
    writer = pd.ExcelWriter(fname)
    dfg.to_excel(writer, 'Sheet1', index=False,startrow=startrow,startcol=startcol)
    dfg.to_excel(writer, 'Sheet2', index=False,startrow=startrow,startcol=startcol)
    writer.save()

# excel multi-tab
def create_files_xls_multiple_helper(cfg_fname):

    df1,df2,df3 = create_files_df_clean()
    write_file_xls(df1,cfg_fname % 'jan')
    write_file_xls(df2,cfg_fname % 'feb')
    write_file_xls(df3,cfg_fname % 'mar')

    return [cfg_fname % 'jan',cfg_fname % 'feb',cfg_fname % 'mar']
    
@pytest.fixture(scope="module")
def create_files_xls_multiple():
    return create_files_xls_multiple_helper(cfg_fname_base_in+'input-xls-mult-%s.xls')

@pytest.fixture(scope="module")
def create_files_xlsx_multiple():
    return create_files_xls_multiple_helper(cfg_fname_base_in+'input-xls-mult-%s.xlsx')
    
#************************************************************
# tests - helpers
#************************************************************

def test_file_extensions_get():
    fname_list = ['a.csv','b.csv']
    ext_list = file_extensions_get(fname_list)
    assert ext_list==['.csv','.csv']
    
    fname_list = ['a.xls','b.xls']
    ext_list = file_extensions_get(fname_list)
    assert ext_list==['.xls','.xls']

def test_file_extensions_all_equal():
    ext_list = ['.csv']*2
    assert file_extensions_all_equal(ext_list)
    ext_list = ['.xls']*2
    assert file_extensions_all_equal(ext_list)
    ext_list = ['.csv','.xls']
    assert not file_extensions_all_equal(ext_list)
    
def test_file_extensions_valid():
    ext_list = ['.csv']*2
    assert file_extensions_valid(ext_list)
    ext_list = ['.xls']*2
    assert file_extensions_valid(ext_list)
    ext_list = ['.exe','.xls']
    assert not file_extensions_valid(ext_list)

#************************************************************
#************************************************************
# scan header
#************************************************************
#************************************************************
def test_csv_header(create_files_csv, create_files_csv_colmismatch, create_files_csv_colreorder):

    with pytest.raises(ValueError) as e:
        c = CombinerCSV([])

    # clean
    combiner = CombinerCSV(fname_list=create_files_csv)
    combiner.sniff_columns()
    assert combiner.is_all_equal()
    assert combiner.is_column_present().all().all()
    assert combiner.sniff_results['columns_all'] == ['date', 'sales', 'cost', 'profit']
    assert combiner.sniff_results['columns_common'] == combiner.sniff_results['columns_all']
    assert combiner.sniff_results['columns_unique'] == []

    # extra column
    combiner = CombinerCSV(fname_list=create_files_csv_colmismatch)
    combiner.sniff_columns()
    assert not combiner.is_all_equal()
    assert not combiner.is_column_present().all().all()
    assert combiner.is_column_present().all().values.tolist()==[True, True, True, True, False]
    assert combiner.sniff_results['columns_all'] == ['date', 'sales', 'cost', 'profit', 'profit2']
    assert combiner.sniff_results['columns_common'] == ['date', 'sales', 'cost', 'profit']
    assert combiner.is_column_present_common().columns.tolist() == ['date', 'sales', 'cost', 'profit']
    assert combiner.sniff_results['columns_unique'] == ['profit2']
    assert combiner.is_column_present_unique().columns.tolist() == ['profit2']

    # mixed order
    combiner = CombinerCSV(fname_list=create_files_csv_colreorder)
    combiner.sniff_columns()
    assert not combiner.is_all_equal()
    assert combiner.sniff_results['df_columns_order']['profit'].values.tolist() == [3, 3, 2]


