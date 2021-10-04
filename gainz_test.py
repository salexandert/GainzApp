from transactions import Transactions
import pandas as pd


if __name__ == "__main__":
    transactions = Transactions(view='./saves/Golden_init.xlsx')

    transactions.auto_link(asset=None, algo="fifo")
    filename_fifo_output = transactions.save(description="Created in gainz_test.py")

    df1 = pd.read_excel('./saves/Golden_fifo.xlsx', sheet_name="All Transactions", usecols=["id", "quantity", "name", "trans_type", "time_stamp", "links"], index_col=0)
    df2 = pd.read_excel(filename_fifo_output, sheet_name="All Transactions", usecols=["id", "quantity", "name", "trans_type", "time_stamp", "links"], index_col=0)

    df1.sort_index(inplace=True)
    df2.sort_index(inplace=True)

    # print(df1.shape)
    # print(df2.shape)

    print(df1.equals(df2))

    print(df1['quantity'].equals(df2['quantity']))
    print(df1['name'].equals(df2['name']))
    print(df1['trans_type'].equals(df2['trans_type']))
    print(df1['time_stamp'].equals(df2['time_stamp']))
    print(df1['links'].equals(df2['links']))

    df_compare = df1['links'].compare(df2['links'], align_axis=1)

    df_compare.to_excel('compare.xlsx') 
 



    # import ipdb
    # ipdb.set_trace()

